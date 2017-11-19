import torch
import torch.nn.functional as F
from torch import nn


def softmax(input, dim=1):
    transposed_input = input.transpose(dim, len(input.size())-1)
    softmaxed_output = F.softmax(transposed_input.contiguous().view(-1, transposed_input.size(-1)))
    return softmaxed_output.view(*transposed_input.size()).transpose(dim, len(input.size())-1)


class CapsuleLayer(nn.Module):
    def __init__(self, num_capsules, num_route_nodes, in_channels, out_channels, kernel_size=None, stride=None, num_iterations=3):
        super(CapsuleLayer, self).__init__()

        self.num_capsules = num_capsules
        self.num_route_nodes = num_route_nodes
        self.num_iterations = num_iterations

        if num_route_nodes != -1:
            # Routing between capsules
            self.route_weights = nn.Parameter(torch.randn(num_capsules, num_route_nodes, in_channels, out_channels))

        else:
            # Lower level is a conv net
            self.capsules = nn.ModuleList([nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size, stride=stride, padding=0) for _ in range(num_capsules)])

        def squash(self, tensor, dim=-1):
            squared_norm = (tensor ** 2).sum(dim=dim, keepdim=True)
            scale = squared_norm / (1 + squared_norm)
            return scale * tensor / torch.squrt(squared_norm)

        def forward(self, x):
            if self.num_route_nodes != -1:
                # Inputs * Weights
                priors = x[None, :, :, None, :] @ self.route_weights[:, None, :, :, :]

                # Routing algorithm
                logits = Variable(torch.zeros(*priors.size())).cuda()
                for i in range(self.num_iterations):
                    probs = softmax(logits, dim=2)
                    outputs = self.squash((probs * priors).sum(dim=2, keepdim=True))

                    if i != self.num_iterations - 1:
                        delta_logits = (priors * outputs).sum(dim=-1, keepdim=True)
                        logits = logits + delta_logits

            else:
                outputs = [capsule(x).view(x.size(0), -1, 1) for capsule in self.capsules]
                outputs = torch.cat(outputs, dim=-1)
                outputs = self.squash(outputs)

            return outputs