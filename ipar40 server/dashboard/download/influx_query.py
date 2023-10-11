query_download = {
    "start_time" : "-1m",
    "stop_time" : "now()",
    "measurements" : ["lathe", "lathe_strings", "lathe_analytics"],
    "aspects" : ["speed", "temperature", "current", "vibration"],
    "variables" : ["rpm", "tempC", "cur", "vibX_fft", "vibY_fft", "vibZ_fft", "vibX_rms", "vibY_rms", "vibZ_rms", "vibX_psd", "vibY_psd", "vibZ_psd"],
}
