import logging
from pathlib import Path

import hydra
import pandas as pd
from omegaconf import DictConfig

from benchmark import cv_train, nlp_infer, nlp_train, cv_infer
PLACES365_DATA_DIR = "places365/"
RESULT_DATA_DIR = "data"

"""
 docker run -v /root/places365_standard/:/workspace/places365/ \
 -v /root/MIGProfiler/data/:/workspace/data/\
 -v /root/MIGProfiler/logs/: /workspace/logs/\
 --net mig_perf --gpus 'device=0:0' --name profiler-container \
 --cap-add SYS_ADMIN --shm-size="15g" mig-perf/profiler:1.0
"""


@hydra.main(version_base=None, config_path='../../configs', config_name='single_instance')
def run(cfgs: DictConfig):
    model_name = cfgs.model_name
    workload = cfgs.workload
    default_batchsize = cfgs.benchmark_plan.default_batchsize
    default_seqlenth = cfgs.benchmark_plan.default_seqlenth
    batch_sizes = cfgs.benchmark_plan.batch_sizes
    seq_lengths = cfgs.benchmark_plan.sequence_lengths
    fixed_time = cfgs.benchmark_plan.fixed_time
    logger = logging.getLogger(f"{model_name}_{workload}")
    ret = None

    if workload == 'cv_infer':
        result = []
        for batch_size in batch_sizes:
            try:
                cv_infer_res = cv_infer(model_name, fixed_time, batch_size, PLACES365_DATA_DIR)
                print(f"result:{cv_infer_res}")
                result.append(cv_infer_res)
            except Exception as e:
                logger.exception(e)
        ret = pd.concat(result)
    if workload == 'cv_train':
        result = []
        for batch_size in batch_sizes:
            try:
                result.append(cv_train(model_name, fixed_time, batch_size, PLACES365_DATA_DIR))
            except Exception as e:
                logger.exception(e)
        ret = pd.concat(result)
    if workload == 'nlp_infer':
        result_seq = []
        for seq_length in seq_lengths:
            try:
                result_seq.append(nlp_infer(model_name, fixed_time, batch_size=default_batchsize, seq_length=seq_length))
            except Exception as e:
                logger.exception(e)
        ret_seq = pd.concat(result_seq)
        result_bsz = []
        for batch_size in batch_sizes:
            try:
                result_bsz.append(nlp_infer(model_name, fixed_time, batch_size=batch_size, seq_length=default_seqlenth))
            except Exception as e:
                logger.exception(e)
        ret_bsz = pd.concat(result_bsz)
        ret = pd.concat([ret_seq, ret_bsz])
    if workload == 'nlp_train':
        result_seq = []
        for seq_length in seq_lengths:
            try:
                result_seq.append(nlp_train(model_name, fixed_time, batch_size=default_batchsize, seq_length=seq_length))
            except Exception as e:
                logger.exception(e)
        ret_seq = pd.concat(result_seq)
        result_bsz = []
        for batch_size in batch_sizes:
            try:
                result_bsz.append(nlp_train(model_name, fixed_time, batch_size=batch_size, seq_length=default_seqlenth))
            except Exception as e:
                logger.exception(e)
        ret_bsz = pd.concat(result_bsz)
        ret = pd.concat([ret_seq, ret_bsz])
    # mount local volumn ./workspace
    save_file = Path(f'{RESULT_DATA_DIR}/{model_name}_{workload}.csv')
    if save_file.exists():
        ret.to_csv(f'{RESULT_DATA_DIR}/{model_name}_{workload}.csv', mode='a', header=False)
    else:
        ret.to_csv(f'{RESULT_DATA_DIR}/{model_name}_{workload}.csv', mode='a', header=True)
    logger.info(f"result: {ret}")
    print(f"final result: {ret}")


if __name__ == '__main__':
    run()

