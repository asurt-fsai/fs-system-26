
import torch
import torch.nn as nn
from typing import Optional
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader
import os

seed = 42
torch.manual_seed(seed)
#torch.cuda.manual_seed(seed)

class Seq2Seq(nn.Module):
    def __init__(self, input_dim=4, hidden_dim=32, output_dim=2, num_layers=3):
        super(Seq2Seq, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.output_dim = output_dim
        self.input_dim = input_dim
        # Encoder
        self.encoder = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
# Decoder
        self.decoder = nn.LSTM(hidden_dim + output_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)

        # Store hidden and cell states
        self.hidden = None
        self.cell = None

    def forward(self, x, target_seq_len = 1):
        batch_size, seq_len, _ = x.shape
        # target_seq_len = seq_len*5
        target_seq_len = 15
        # Encode
        _, (hidden, cell) = self.encoder(x, (self.hidden, self.cell) if self.hidden is not None else None)

        # Store states for future sequences

        self.hidden, self.cell = None,None #This line can be changed to make the model persists state between forward passes.
        # this


        # Prepare decoder input (first input as zeros)
        decoder_input = torch.zeros(batch_size, 1, self.hidden_dim + self.output_dim, device=x.device)
        outputs = []

        for _ in range(target_seq_len):
            decoder_output, (hidden, cell) = self.decoder(decoder_input, (hidden, cell))
            output = self.fc(decoder_output[:, -1, :])  # Get last time step output
            outputs.append(output.unsqueeze(1))

            # Update decoder input with the last output
            decoder_input = torch.cat((decoder_output, output.unsqueeze(1)), dim=-1)

        return torch.cat(outputs, dim=1)

    def empty_state(self):
      self.hidden, self.cell = None, None

    def predict(self, x):
        # Add batch dimension (batch_size=1) if not present
        if x.dim() == 2:
            x = x.unsqueeze(0)  # (1, seq_len, 5)
        
        batch_size, seq_len, _ = x.shape
        target_seq_len = 15
        
        
        # Encode
        _, (hidden, cell) = self.encoder(x, (self.hidden, self.cell) if self.hidden is not None else None)
        
        # Store states for future sequences
        self.hidden, self.cell = None, None  # This line can be changed to make the model persist state
        
        # Prepare decoder input (first input as zeros)
        decoder_input = torch.zeros(1, 1, self.hidden_dim + self.output_dim, device=x.device)
        outputs = []
        
        for _ in range(target_seq_len):
            decoder_output, (hidden, cell) = self.decoder(decoder_input, (hidden, cell))
            output = self.fc(decoder_output[:, -1, :])  # Get last time step output
            outputs.append(output)
            
            # Update decoder input with the last output
            decoder_input = torch.cat((decoder_output, output.unsqueeze(1)), dim=-1)
        
        # Stack outputs and remove batch dimension if input didn't have one
        outputs = torch.stack(outputs, dim=1)  # (1, target_seq_len, output_dim)
        if x.dim() == 2:
            outputs = outputs.squeeze(0)  # (target_seq_len, output_dim)
        
        return outputs


def createModel(path: str) -> Seq2Seq:
    """
    Create a planning model from a saved state dict

    Parameters
    ----------
    path : str
        Path to the saved state dict

    Returns
    -------
    MyPlannerTransformer
        Planning model with the saved state dict loaded
    """
    model = Seq2Seq()
    model.load_state_dict(torch.load(path, map_location=torch.device('cpu')))

    #model.cuda()
    return model



def createModel(path: str, device='cpu') -> Seq2Seq:
    # Check if the model name indicates it is colorless
    input_dim = 2 if "colorless" in path.lower() else 4
    model = Seq2Seq(input_dim=input_dim)

    checkpoint = torch.load(path, map_location=device)
    
    # Handle both full checkpoints and raw state_dicts
    if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
        model.load_state_dict(checkpoint['model_state_dict'])
    else:
        model.load_state_dict(checkpoint)

    model.to(device)
    model.eval()   # VERY important for inference

    return model