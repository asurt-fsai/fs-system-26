# import tensorrt as trt
# import pycuda.driver as cuda
# import numpy as np

# # Monkey-patch np.bool to fix incompatibility with tensorrt/pycuda on newer numpy versions
# np.bool = np.bool_

# class TensorRTModel:
#     """
#     TensorRT inference wrapper.

#     IMPORTANT: A CUDA context must be active on the calling thread BEFORE
#     constructing this class.  Do one of:
#         • import pycuda.autoinit          (single-thread / single-process only)
#         • cuda.init(); dev = cuda.Device(0); ctx = dev.make_context()

#     The old top-level `import pycuda.autoinit` was removed because it binds
#     the CUDA context to the importing thread, which breaks multi-threaded
#     and multi-process designs.
#     """

#     def __init__(self, engine_path):
#         """
#         Initialize the TensorRT model.
#         Loads the engine, creates execution context, and allocates GPU memory.
#         """
#         self.logger = trt.Logger(trt.Logger.WARNING)

#         # Load the TRT engine
#         with open(engine_path, "rb") as f, trt.Runtime(self.logger) as runtime:
#             self.engine = runtime.deserialize_cuda_engine(f.read())

#         self.context = self.engine.create_execution_context()

#         # Allocate buffers
#         self.inputs = []
#         self.outputs = []
#         self.bindings = []
#         self.stream = cuda.Stream()

#         for binding in self.engine:
#             size = trt.volume(self.engine.get_binding_shape(binding))
#             dtype = trt.nptype(self.engine.get_binding_dtype(binding))

#             # Allocate host and device buffers
#             host_mem = cuda.pagelocked_empty(size, dtype)
#             device_mem = cuda.mem_alloc(host_mem.nbytes)

#             self.bindings.append(int(device_mem))

#             if self.engine.binding_is_input(binding):
#                 self.inputs.append({
#                     'host': host_mem,
#                     'device': device_mem,
#                     'shape': self.engine.get_binding_shape(binding),
#                     'dtype': dtype
#                 })
#             else:
#                 self.outputs.append({
#                     'host': host_mem,
#                     'device': device_mem,
#                     'shape': self.engine.get_binding_shape(binding),
#                     'dtype': dtype
#                 })

#     def predict(self, x_numpy):
#         """
#         Run inference using the TensorRT engine.
#         Accepts a numpy array of shape (10, 4) or (1, 10, 4).
#         Returns a numpy array of shape (1, 15, 2).
#         """
#         # Ensure input has the batch dimension: (1, 10, 4)
#         if x_numpy.ndim == 2:
#             x_numpy = np.expand_dims(x_numpy, axis=0)

#         # Ensure it's the correct dtype (usually float32)
#         x_numpy = np.ascontiguousarray(x_numpy, dtype=self.inputs[0]['dtype'])

#         # Copy input data to host buffer
#         np.copyto(self.inputs[0]['host'], x_numpy.ravel())

#         # Transfer input data to the GPU
#         cuda.memcpy_htod_async(self.inputs[0]['device'], self.inputs[0]['host'], self.stream)

#         # Run inference
#         self.context.execute_async_v2(bindings=self.bindings, stream_handle=self.stream.handle)

#         # Transfer predictions back from the GPU
#         cuda.memcpy_dtoh_async(self.outputs[0]['host'], self.outputs[0]['device'], self.stream)

#         # Synchronize the stream
#         self.stream.synchronize()

#         # Format the output shape (1, 15, 2)
#         output_shape = self.outputs[0]['shape']
#         out = self.outputs[0]['host'].reshape(output_shape)

#         # Return a copy so the caller's reference is safe even if predict()
#         # is called again (which overwrites the pagelocked host buffer).
#         return out.copy()

import numpy as np
import tensorrt as trt
import pycuda.driver as cuda

# Compatibility fix for newer NumPy
np.bool = np.bool_


class TensorRTModel:
    """
    TensorRT inference wrapper for TensorRT 10/11 name-based API.

    Expected input:
        x_numpy shape (10, 4) or (1, 10, 4)

    Expected output:
        shape (1, 15, 2)
    """

    def __init__(self, engine_path):
        self.logger = trt.Logger(trt.Logger.WARNING)

        with open(engine_path, "rb") as f, trt.Runtime(self.logger) as runtime:
            self.engine = runtime.deserialize_cuda_engine(f.read())

        if self.engine is None:
            raise RuntimeError(
                f"Failed to deserialize TensorRT engine: {engine_path}. "
                "The engine may be incompatible with this TensorRT/CUDA/GPU environment."
            )

        self.context = self.engine.create_execution_context()
        if self.context is None:
            raise RuntimeError("Failed to create TensorRT execution context.")

        self.stream = cuda.Stream()

        self.inputs = []
        self.outputs = []
        self.device_allocations = {}

        # TensorRT 10/11 uses IO tensor names instead of old binding APIs
        for i in range(self.engine.num_io_tensors):
            name = self.engine.get_tensor_name(i)
            mode = self.engine.get_tensor_mode(name)
            dtype = trt.nptype(self.engine.get_tensor_dtype(name))

            shape = tuple(self.engine.get_tensor_shape(name))

            # This engine should be static: input (1, 10, 4), output (1, 15, 2)
            if any(dim < 0 for dim in shape):
                raise RuntimeError(
                    f"Dynamic shape detected for tensor '{name}': {shape}. "
                    "This wrapper currently expects static shapes."
                )

            size = trt.volume(shape)

            host_mem = cuda.pagelocked_empty(size, dtype)
            device_mem = cuda.mem_alloc(host_mem.nbytes)

            self.device_allocations[name] = device_mem

            tensor_info = {
                "name": name,
                "host": host_mem,
                "device": device_mem,
                "shape": shape,
                "dtype": dtype,
            }

            if mode == trt.TensorIOMode.INPUT:
                self.inputs.append(tensor_info)
            elif mode == trt.TensorIOMode.OUTPUT:
                self.outputs.append(tensor_info)

            # Required for execute_async_v3
            self.context.set_tensor_address(name, int(device_mem))

        if len(self.inputs) != 1:
            raise RuntimeError(f"Expected 1 input tensor, found {len(self.inputs)}")

        if len(self.outputs) != 1:
            raise RuntimeError(f"Expected 1 output tensor, found {len(self.outputs)}")

        print("TensorRT engine loaded.")
        print("Input tensor :", self.inputs[0]["name"], self.inputs[0]["shape"], self.inputs[0]["dtype"])
        print("Output tensor:", self.outputs[0]["name"], self.outputs[0]["shape"], self.outputs[0]["dtype"])

    def predict(self, x_numpy):
        """
        Run inference.

        Accepts:
            (10, 4) or (1, 10, 4)

        Returns:
            (1, 15, 2)
        """

        if x_numpy.ndim == 2:
            x_numpy = np.expand_dims(x_numpy, axis=0)

        expected_shape = self.inputs[0]["shape"]

        if tuple(x_numpy.shape) != tuple(expected_shape):
            raise RuntimeError(
                f"Wrong input shape. Expected {expected_shape}, got {x_numpy.shape}"
            )

        x_numpy = np.ascontiguousarray(x_numpy, dtype=self.inputs[0]["dtype"])

        np.copyto(self.inputs[0]["host"], x_numpy.ravel())

        cuda.memcpy_htod_async(
            self.inputs[0]["device"],
            self.inputs[0]["host"],
            self.stream,
        )

        ok = self.context.execute_async_v3(stream_handle=self.stream.handle)
        if not ok:
            raise RuntimeError("TensorRT execute_async_v3 failed.")

        cuda.memcpy_dtoh_async(
            self.outputs[0]["host"],
            self.outputs[0]["device"],
            self.stream,
        )

        self.stream.synchronize()

        output_shape = self.outputs[0]["shape"]
        out = self.outputs[0]["host"].reshape(output_shape)

        return out.copy()