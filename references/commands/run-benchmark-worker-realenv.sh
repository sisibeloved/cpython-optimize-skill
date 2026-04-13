# 真实环境：直接执行单个 run_benchmark.py

# 说明：
# - 这是 CinderX/ARM 真实环境中用于单 benchmark worker 复现与定位的参考命令
# - 重点是 worker 参数、JIT 日志和 HIR dump
# - 这类命令本身就应作为 HIR 分析入口，不要再额外发明一条“简化分析命令”

PYTHONJITENABLEJITLISTWILDCARDS=1 \
PYTHONJITLISTFILE=/home/jit_list.txt \
PYTHONPATH="$PWD/scripts/arm/pyperf_env_hook:$PYTHONPATH" \
PYTHONJITDUMPHIR=1 \
PYTHONJITDUMPSTATS=1 \
PYTHONJITLOGFILE="/home/jit-go.log" \
PYTHONJITDUMPFINALHIR=1 \
PYTHONJITTYPEANNOTATIONGUARDS=1 \
PYTHONJITENABLEHIRINLINER=1 \
PYTHONJITAUTO=2 \
PYTHONJITSPECIALIZEDOPCODES=1 \
python /usr/local/lib/python3.14/site-packages/pyperformance/data-files/benchmarks/bm_go/run_benchmark.py --worker -l5 -w11 -n2
