
query_home = {
    "start_time" : "-1m",
    "stop_time" : "now()",
    "measurements" : ["lathe", "lathe_strings", "lathe_analytics"],
    "aspects" : ["speed", "temperature", "current", "vibration"],
    "variables" : ["rpm", "tempC", "cur", "vibX_fft", "vibY_fft", "vibZ_fft"],
}

query_analytics = {
    "start_time" : "-1m",
    "stop_time" : "now()",
    "measurements" : ["lathe", "lathe_strings", "lathe_analytics"],
    "aspects" : ["speed", "temperature", "current", "vibration"], 
    "variables" : ["rpm", "tempC", "cur", "vibX_rms", "vibY_rms", "vibZ_rms", "vibX_psd", "vibY_psd", "vibZ_psd"],
    "record_count" : "20",
}

home_measurements = ["lathe", "lathe_strings", "lathe_analytics"]
home_aspects = ["rpm", "current", "tempC", "vibX", "vibY", "vibZ"]



topic = "bmetk/markk/lathe_analytics//backend"
