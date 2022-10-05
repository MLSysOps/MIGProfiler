export PYTHONPATH="${PWD}"
batch_sizes=(1 2 4 8 16 32 64 128 256)

function batch_size_benchmark {
  for batch_size in ${batch_sizes[*]}
  do
      CUDA_VISIBLE_DEVICES=${1} python ./src/A100-cv-infer_test.py \
      "model_name=${2}" "mig_profile=${3}" "batch_size=${batch_size}" "gpu=${4}"\
      "result_dir=${5}"
  done
  return 0
}

batch_size_benchmark "$1" "$2" "$3" "$4" "$5"