# 真实环境：pyperformance run 单用例

# 说明：
# - 这是 CinderX/ARM 真实环境中用于 `python -m pyperformance run` 的参考命令
# - 重点是 `warmup`、环境变量和 `--inherit-environ` 的口径
# - 如果要 dump HIR，优先在这条真实命令上追加 debug 环境变量，不要另起一条分析命令

PYTHONJITENABLEJITLISTWILDCARDS=1 \
PYTHONJITLISTFILE=/home/jit_list.txt \
PYTHONPATH="$PWD/scripts/arm/pyperf_env_hook:$PYTHONPATH" \
PYTHONJITTYPEANNOTATIONGUARDS=1 \
PYTHONJITENABLEHIRINLINER=1 \
PYTHONJITAUTO=2 \
PYTHONJITSPECIALIZEDOPCODES=1 \
python -m pyperformance run --affinity=262 --warmup 3 -b regex_compile \
  --inherit-environ http_proxy,https_proxy,LD_LIBRARY_PATH,PYTHONJITAUTO,PYTHONJITSPECIALIZEDOPCODES,PYTHONJITENABLEHIRINLINER,PYTHONJITTYPEANNOTATIONGUARDS,PYTHONPATH,PYTHONJITLISTFILE,PYTHONJITENABLEJITLISTWILDCARDS
