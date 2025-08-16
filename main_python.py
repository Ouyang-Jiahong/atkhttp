from PythonRunner import open_atk, send_atk_command, close_atk

if __name__ == "__main__":
    base = "http://localhost:8080"
    open_atk(base, "127.0.0.1", 6655)
    # （1）场景与时间
    print(send_atk_command(base, "New", "/ Scenario SimpleScenario"))
    send_atk_command(base, "SetAnalysisTimePeriod", "* \"1 Jan 2025 00:00:00.00\" \"5 Jan 2025 00:00:00.00\"");
    send_atk_command(base, "Animate", "* Reset");

    # （2）地面站
    send_atk_command(base, "New", "/ Facility GroundStation1");
    send_atk_command(base, "SetPosition", "*/Facility/GroundStation1 Geodetic 39.9 116.4 50.0");

    # （3）卫星
    send_atk_command(base, "New", "/ Satellite Sat1");
    send_atk_command(base, "SetState", "*/Satellite/Sat1 Classical TwoBody NoProp 60.0 J2000 \"2025-01-01 00:00:00.000\" 6878136.999999994412065 0.0 44.997423212349375 359.818801881724369 0 359.80316033301915");

    send_atk_command(base, "New", "/ Satellite Sat2");
    send_atk_command(base, "SetState", "*/Satellite/Sat2 Classical TwoBody NoProp 60.0 J2000 \"2025-01-01 00:00:00.000\" 6853454.382262638770044 0.0 98.137200680920444 100.582578708373092 0 0.023861912010873");

    # （4）传感器
    send_atk_command(base, "New", "/ Facility/GroundStation1/Sensor GroundSensor1");
    send_atk_command(base, "Define", "*/Facility/GroundStation1/Sensor/GroundSensor1 SimpleCone 30");
    send_atk_command(base, "Point", "*/Facility/GroundStation1/Sensor/GroundSensor1 Fixed Quaternion 0 0 0 -1");

    # （5）可见性 + 报表（示例）
    print(send_atk_command(base, "Access", "*/Satellite/Sat2 */Satellite/Sat1 TimePeriod \"1 Jan 2025 00:00:00.00\" \"5 Jan 2025 00:00:00.00\""))
    print(send_atk_command(base, "Report_RM", "*/Satellite/Sat2 Style \"Access\" Type Export File \"D:\\\\Codes\\\\atk-java-demo\\\\report\\\\Access.txt\" AccessObject */Satellite/Sat1 TimePeriod \"1 Jan 2025 00:00:00.00\" \"5 Jan 2025 00:00:00.00\" TimeStep 60"))

    # 可选：保存场景
    send_atk_command(base, "Save", "/ *");
    close_atk(base)
