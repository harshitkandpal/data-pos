import torch
import torchvision.models as models

# Load pretrained models
resnet = models.resnet18(weights="IMAGENET1K_V1")
mobilenet = models.mobilenet_v2(weights="IMAGENET1K_V1")
alexnet = models.alexnet(weights="IMAGENET1K_V1")

# Save them as files
torch.save(resnet.state_dict(), "resnet18.pth")
torch.save(mobilenet.state_dict(), "mobilenet_v2.pth")
torch.save(alexnet.state_dict(), "alexnet.pth")

print("Models saved!")