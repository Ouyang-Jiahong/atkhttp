from atk_python_sdk import atkOpen, atkConnect, atkClose

if __name__ == "__main__":
    base = "http://localhost:8080"
    atkOpen(base, "127.0.0.1", 6655)

    # atkConnect(base, "Access", "*/Satellite/Sat2 */Satellite/Sat1 TimePeriod \"1 Jan 2025 00:00:00.00\" \"5 Jan 2025 00:00:00.00\"")
    # atkConnect(base, "Report_RM", "*/Satellite/Sat2 Style \"Access\" Type Display AccessObject */Satellite/Sat1 TimePeriod \"1 Jan 2025 00:00:00.00\" \"5 Jan 2025 00:00:00.00\" TimeStep 60")

    atkConnect(base, "AER", "*/Satellite/Sat2 */Satellite/Sat1 TimePeriod \"1 Jan 2025 00:00:00.00\" \"5 Jan 2025 00:00:00.00\"")
    atkConnect(base, "Report_RM", "*/Satellite/Sat2 Style \"AER\" Type Display AccessObject */Satellite/Sat1 TimePeriod \"1 Jan 2025 00:00:00.00\" \"5 Jan 2025 00:00:00.00\" TimeStep 60")

    # （1）场景与时间
    print(atkConnect(base, "New", "/ Scenario SimpleScenario"))
    atkConnect(base, "SetAnalysisTimePeriod", "* \"1 Jan 2025 00:00:00.00\" \"5 Jan 2025 00:00:00.00\"");
    atkConnect(base, "Animate", "* Reset");

    # （2）地面站
    atkConnect(base, "New", "/ Facility GroundStation1");
    atkConnect(base, "SetPosition", "*/Facility/GroundStation1 Geodetic 39.9 116.4 50.0");

    # （3）卫星
    atkConnect(base, "New", "/ Satellite Sat1");
    atkConnect(base, "SetState", "*/Satellite/Sat1 Classical TwoBody NoProp 60.0 J2000 \"2025-01-01 00:00:00.000\" 6878136.999999994412065 0.0 44.997423212349375 359.818801881724369 0 359.80316033301915");

    atkConnect(base, "New", "/ Satellite Sat2");
    atkConnect(base, "SetState", "*/Satellite/Sat1 Classical TwoBody NoProp 60.0 J2000 \"2025-01-01 00:00:00.000\" 9878136.999999994412065 0.0 44.997423212349375 359.818801881724369 0 359.80316033301915");

    # （4）传感器
    atkConnect(base, "New", "/ Facility/GroundStation1/Sensor GroundSensor1");
    atkConnect(base, "Define", "*/Facility/GroundStation1/Sensor/GroundSensor1 SimpleCone 30");
    atkConnect(base, "Point", "*/Facility/GroundStation1/Sensor/GroundSensor1 Fixed Quaternion 0 0 0 -1");

    # （5）可见性 + 报表（示例）
    print(atkConnect(base, "Access", "*/Satellite/Sat2 */Satellite/Sat1 TimePeriod \"1 Jan 2025 00:00:00.00\" \"5 Jan 2025 00:00:00.00\""))
    print(atkConnect(base, "Report_RM", "*/Satellite/Sat2 Style \"Access\" Type Display AccessObject */Satellite/Sat1 TimePeriod \"1 Jan 2025 00:00:00.00\" \"5 Jan 2025 00:00:00.00\" TimeStep 60"))

    # 可选：保存场景
    atkConnect(base, "Save", "/ *");
    atkClose(base)
