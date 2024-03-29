#! /usr/bin/env bash
GPU_ID=0
MODEL_NAME='resnet50'
NUM_TEST_BATCHES=1000
MIG_PROFILE='7g.80gb'
CIS=('1c' '2c' '3c' '4c' '')
BATCH_SIZES=(1 2 4 8 16 32 64)

EXP_SAVE_DIR="${PWD}"
cd ../../mig_perf/inference
export PYTHONPATH="${PWD}"

echo 'Enable MIG'
sudo nvidia-smi -i "${GPU_ID}" -mig 1
# Try different MIG profiles
for CI in "${CIS[@]}"; do
  echo '=========================================================='
  echo " * Compute Instance Num = ${CI}"
  echo '=========================================================='
  sudo nvidia-smi mig -i "${GPU_ID}" -cgi "${MIG_PROFILE}"
  sudo nvidia-smi mig -i "${GPU_ID}" -cci "${CI}.${MIG_PROFILE}"

  echo 'Start DCGM'
  docker run -d --rm --gpus all --net mig_perf -p 9400:9400  \
    -v "${EXP_SAVE_DIR}/../../mig_perf/inference/client/dcp-metrics-included.csv:/etc/dcgm-exporter/customized.csv" \
    --name dcgm_exporter --cap-add SYS_ADMIN   nvcr.io/nvidia/k8s/dcgm-exporter:2.4.7-2.6.11-ubuntu20.04 \
    -c 500 -f /etc/dcgm-exporter/customized.csv -d f
  sleep 3
  docker ps

  # iterate through batch size list
  for BATCH_SIZE in "${BATCH_SIZES[@]}"; do
    echo "Batch size ${BATCH_SIZE}"
    echo 'Start profiling client 0'
    python client/block_inference_cv.py -b "${BATCH_SIZE}" -m "${MODEL_NAME}" -n "${NUM_TEST_BATCHES}" \
      -i "${GPU_ID}" -mi 0 -dbn "${EXP_SAVE_DIR}/batch_size/${CI:-7c}.${MIG_PROFILE}"

    echo 'Finish!'
    sleep 10
  done

  echo 'Stop DCGM'
  docker stop dcgm_exporter

  sudo nvidia-smi mig -i "${GPU_ID}" -dci
  sudo nvidia-smi mig -i "${GPU_ID}" -dgi

  sleep 10
done
sudo nvidia-smi -i "${GPU_ID}" -mig 0
echo 'Disable MIG'
