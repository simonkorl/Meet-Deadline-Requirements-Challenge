from run_this import evaluate

def test_reno():
    block_traces = ["datasets/application_traces/data_video.csv", "datasets/application_traces/data_audio.csv"]
    network_trace = "datasets/network_traces/trace.txt"
    log_packet_file = "output/packet_log/packet-0.log"
    solution_file = 'solution_demos.reno.solution'
    evaluate(solution_file, block_traces, network_trace, log_packet_file)

def test_rl_torch():
    block_traces = ["datasets/application_traces/data_video.csv", "datasets/application_traces/data_audio.csv"]
    network_trace = "datasets/network_traces/trace.txt"
    log_packet_file = "output/packet_log/packet-0.log"
    solution_file = 'solution_demos.rl_torch.solution'
    evaluate(solution_file, block_traces, network_trace, log_packet_file)

def test_rl_tensorflow():
    block_traces = ["datasets/application_traces/data_video.csv", "datasets/application_traces/data_audio.csv"]
    network_trace = "datasets/network_traces/trace.txt"
    log_packet_file = "output/packet_log/packet-0.log"
    solution_file = 'solution_demos.rl_tensorflow.solution'
    evaluate(solution_file, block_traces, network_trace, log_packet_file)
