#!/usr/bin/env python3

import torch
import onnx
from model import Seq2Seq


PT_PATH = "./Completed_Models/best_model.pt"
ONNX_PATH = "./Completed_Models/best_model.onnx"


def main():
    # Your ROS node uses colored cones:
    # each cone = [x_model, y_model, blue_flag, yellow_flag]
    # so input_dim must be 4.
    model = Seq2Seq(
        input_dim=4,
        hidden_dim=32,
        output_dim=2,
        num_layers=3,
    )

    # Load the saved weights
    state_dict = torch.load(PT_PATH, map_location="cpu")

    # Remove "module." prefix if the model was trained with DataParallel
    clean_state_dict = {}
    for k, v in state_dict.items():
        if k.startswith("module."):
            clean_state_dict[k[len("module."):]] = v
        else:
            clean_state_dict[k] = v

    # Use strict=True because we want to be sure the architecture matches exactly
    model.load_state_dict(clean_state_dict, strict=True)
    model.eval()
    model.empty_state()

    # This must match your ROS node:
    # cones_array after padding has shape (10, 4)
    # TensorRT predict() adds batch dimension, so final input is (1, 10, 4)
    dummy_input = torch.randn(1, 10, 4, dtype=torch.float32)

    # Test PyTorch output before exporting
    with torch.no_grad():
        torch_output = model(dummy_input)

    print("PyTorch output shape:", tuple(torch_output.shape))

    if tuple(torch_output.shape) != (1, 15, 2):
        raise RuntimeError(
            f"Expected output shape (1, 15, 2), got {tuple(torch_output.shape)}"
        )

    # Export to ONNX
    torch.onnx.export(
        model,
        dummy_input,
        ONNX_PATH,
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=["cones"],
        output_names=["path"],
    )

    print(f"Exported ONNX model to: {ONNX_PATH}")

    # Verify ONNX file
    onnx_model = onnx.load(ONNX_PATH)
    onnx.checker.check_model(onnx_model)

    print("ONNX check passed.")


if __name__ == "__main__":
    main()