#!/usr/bin/env python3
import os

import aws_cdk as cdk
from be.be_stack import BeStack

REGION = "ap-southeast-1"

app = cdk.App()
BeStack(app, "BeStack",
        env=cdk.Environment(account='849218053739', region='ap-southeast-1'),
)

app.synth()
