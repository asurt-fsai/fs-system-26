import tensorrt as trt
import pycuda.driver as cuda
import numpy as np

# Monkey-patch np.bool to fix incompatibility with tensorrt/pycuda on newer numpy versions
np.bool = np.bool_

class TensorRTModel:
    """
    TensorRT inference wrapper.

    IMPORTANT: A CUDA context must be active on the calling thread BEFORE
    constructing this class.  Do one of:
        • import pycuda.autoinit          (single-thread / single-process only)
        • cuda.init(); dev = cuda.Device(0); ctx = dev.make_context()

    The old top-level `import pycuda.autoinit` was removed because it binds
    the CUDA context to the importing thread, which breaks multi-threaded
    and multi-process designs.
    """

    def __init__(self, engine_path):
        """
        Initialize the TensorRT model.
        Loads the engine, creates execution context, and allocates GPU memory.
        """
        self.logger = trt.Logger(trt.Logger.WARNING)

        # Load the TRT engine
        with open(engine_path, "rb") as f, trt.Runtime(self.logger) as runtime:
            self.engine = runtime.deserialize_cuda_engine(f.read())

        self.context = self.engine.create_execution_context()

        # Allocate buffers
        self.inputs = []
        self.outputs = []
        self.bindings = []
        self.stream = cuda.Stream()

        for binding in self.engine:
            size = trt.volume(self.engine.get_binding_shape(binding))
            dtype = trt.nptype(self.engine.get_binding_dtype(binding))

            # Allocate host and device buffers
            host_mem = cuda.pagelocked_empty(size, dtype)
            device_mem = cuda.mem_alloc(host_mem.nbytes)

            self.bindings.append(int(device_mem))

            if self.engine.binding_is_input(binding):
                self.inputs.append({
                    'host': host_mem,
                    'device': device_mem,
                    'shape': self.engine.get_binding_shape(binding),
                    'dtype': dtype
                })
            else:
                self.outputs.append({
                    'host': host_mem,
                    'device': device_mem,
                    'shape': self.engine.get_binding_shape(binding),
                    'dtype': dtype
                })

    def predict(self, x_numpy):
        """
        Run inference using the TensorRT engine.
        Accepts a numpy array of shape (10, 4) or (1, 10, 4).
        Returns a numpy array of shape (1, 15, 2).
        """
        # Ensure input has the batch dimension: (1, 10, 4)
        if x_numpy.ndim == 2:
            x_numpy = np.expand_dims(x_numpy, axis=0)

        # Ensure it's the correct dtype (usually float32)
        x_numpy = np.ascontiguousarray(x_numpy, dtype=self.inputs[0]['dtype'])

        # Copy input data to host buffer
        np.copyto(self.inputs[0]['host'], x_numpy.ravel())

        # Transfer input data to the GPU
        cuda.memcpy_htod_async(self.inputs[0]['device'], self.inputs[0]['host'], self.stream)

        # Run inference
        self.context.execute_async_v2(bindings=self.bindings, stream_handle=self.stream.handle)

        # Transfer predictions back from the GPU
        cuda.memcpy_dtoh_async(self.outputs[0]['host'], self.outputs[0]['device'], self.stream)

        # Synchronize the stream
        self.stream.synchronize()

        # Format the output shape (1, 15, 2)
        output_shape = self.outputs[0]['shape']
        out = self.outputs[0]['host'].reshape(output_shape)

        # Return a copy so the caller's reference is safe even if predict()
        # is called again (which overwrites the pagelocked host buffer).
        return out.copy()