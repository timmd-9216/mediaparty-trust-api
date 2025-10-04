#!/bin/bash
source ~/miniforge3/bin/activate
conda activate mediaparty-trust
uvicorn mediaparty_trust_api.main:app --reload

