"""Real pretrained multilingual encoder with trainable sentence and token heads."""
import torch
from torch import nn
from transformers import AutoConfig, AutoModel
from schema import LABELS

class MeaningModel(nn.Module):
    def __init__(self, base, train_layers=4, pretrained=True):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(base, local_files_only=True, use_safetensors=True, add_pooling_layer=False, attn_implementation='eager') if pretrained else AutoModel.from_config(AutoConfig.from_pretrained(base,local_files_only=True),attn_implementation='eager')
        for p in self.encoder.parameters(): p.requires_grad=False
        if train_layers:
            for layer in self.encoder.encoder.layer[-train_layers:]:
                for p in layer.parameters():p.requires_grad=True
        h=self.encoder.config.hidden_size
        self.classifier=nn.Sequential(nn.Dropout(.1),nn.Linear(h*3,256),nn.GELU(),nn.Dropout(.1),nn.Linear(256,len(LABELS)+1))
        self.error_head=nn.Linear(h,1)
        self.scope_head=nn.Linear(h,3)

    def forward(self,input_ids,attention_mask,side_ids):
        hidden=self.encoder(input_ids=input_ids,attention_mask=attention_mask).last_hidden_state
        def pool(side):
            mask=((side_ids==side)&attention_mask.bool()).unsqueeze(-1).to(hidden.dtype)
            return (hidden*mask).sum(1)/mask.sum(1).clamp(min=1)
        pooled=torch.cat([hidden[:,0],pool(0),pool(1)],dim=1)
        return self.classifier(pooled),self.error_head(hidden).squeeze(-1),self.scope_head(hidden),pooled

def masked_bce(logits,labels,positive_weight=None):
    known=labels>=0
    loss=nn.functional.binary_cross_entropy_with_logits(logits,labels.clamp(min=0),pos_weight=positive_weight,reduction='none')
    return (loss*known).sum()/known.sum().clamp(min=1)
