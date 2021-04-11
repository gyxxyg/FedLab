# -*- coding: utf-8 -*-
# @Time    : 4/10/21 3:30 PM
# @Author  : Siqi Liang
# @Contact : zszxlsq@gmail.com
# @File    : test_serialization.py
# @Software: PyCharm
import os
import unittest
import torch
import torch.nn as nn
from fedlab_core.utils import serialization


class Net(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super(Net, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        out = self.fc1(x)
        out = self.relu(out)
        out = self.fc2(out)
        return out


class SerializationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # DO NOT change the setting below, the model is pretrained on MNIST
        cls.input_size = 784
        cls.hidden_size = 250
        cls.num_classes = 10
        test_path = os.path.dirname(os.path.realpath(__file__))
        model_path = os.path.join(test_path, 'data/nnModel.ckpt')
        cls.model = Net(cls.input_size, cls.hidden_size, cls.num_classes)
        cls.model.load_state_dict(torch.load(model_path))

    def _model_params_eq(self, model1, model2):
        for param1, param2 in zip(model1.parameters(), model2.parameters()):
            self.assertTrue(torch.equal(param1, param2))

    def _model_params_neq(self, model1, model2):
        flags = []
        for param1, param2 in zip(model1.parameters(), model2.parameters()):
            flags.append(torch.equal(param1, param2))
        self.assertIn(False, flags)  # at least one False in flags

    @torch.no_grad()
    def test_ravel_model_params_cpu(self):
        cpu_s_params = serialization.ravel_model_params(self.model, cuda=False)
        m_params = torch.Tensor([0])
        for param in self.model.parameters():
            m_params = torch.cat((m_params, param.data.view(-1)))
        m_params = m_params[1:]
        self.assertTrue(torch.equal(cpu_s_params, m_params))

    @torch.no_grad()
    @unittest.skipUnless(torch.cuda.is_available(), 'No GPU was detected')
    def test_ravel_model_params_gpu(self):
        gpu_s_params = serialization.ravel_model_params(self.model, cuda=True)
        m_params = torch.Tensor([0]).cuda()
        for param in self.model.parameters():
            m_params = torch.cat((m_params, param.data.view(-1)))
        m_params = m_params[1:]
        self.assertTrue(torch.equal(gpu_s_params, m_params))

    @torch.no_grad()
    def test_unravel_model_params(self):
        model = Net(self.input_size, self.hidden_size, self.num_classes)
        self._model_params_neq(self.model, model)
        s_params = serialization.ravel_model_params(self.model, cuda=False)
        serialization.unravel_model_params(model, s_params)
        self._model_params_eq(self.model, model)
