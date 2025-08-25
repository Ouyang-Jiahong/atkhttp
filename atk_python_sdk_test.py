from atk_python_sdk import atkOpen, atkConnect, atkClose

if __name__ == "__main__":
    base = "http://localhost:8080"
    # 连接 ATK
    color_num = 1
    atkOpen(base, "127.0.0.1", 6655)

    # 创建场景、设置场景时间
    atkConnect(base, "New", "/", "Scenario SimpleScenario")
    atkConnect(base, "SetAnalysisTimePeriod", "*", '"1 Jan 2025 00:00:00.000" "5 Jan 2025 00:00:00.000"')
    atkConnect(base, "Animate", "*", "Reset")

    # 使用 TLE 创建卫星
    tle1 = "1 99001U 25001A   25197.00000000  .00001200  00000-0  90000-4 0  9997"
    tle2 = "2 99001  97.4000  45.0000 0009000  90.0000 270.0000 13.20000000  1000"
    atkConnect(base, "New", "/", "Satellite sat_tle")
    atkConnect(base, "SetState", "*/Satellite/sat_tle", f'TLE "{tle1}" "{tle2}"')
    atkConnect(base, "Graphics", "*/Satellite/sat_tle", f'SetColor {color_num}')
    color_num = color_num + 1
    atkConnect(base, "Animate", "*", "Reset")


    # 使用 轨道六根数 创建卫星
    atkConnect(base, "New", "/", "Satellite sat_para")
    atkConnect(base, "SetState", '*/Satellite/sat_para', 'Classical TwoBody "1 Jan 2025 00:00:00.000" "5 Jan 2025 00:00:00.000" 60 J2000 "1 Jan 2025 00:00:00.000" 6678137 0 28.5 0 0 0')
    atkConnect(base, "Graphics", "*/Satellite/sat_para", f'SetColor {color_num}')
    color_num = color_num + 1
    atkConnect(base, "Animate", "*", "Reset")

    # 创建地面站
    atkConnect(base, "New", "/", "Facility GroundStation1")
    atkConnect(base, "SetPosition", "*/Facility/GroundStation1", "Geodetic 39.9 116.4 50.0")
    atkConnect(base, "Graphics", "*/Facility/GroundStation1", f'SetColor {color_num}')
    color_num = color_num + 1
    atkConnect(base, "SetConstraint", "*/Facility/GroundStation1", 'AzimuthAngle Min -180.0 Max 180.0 ExcludeIntervals')
    atkConnect(base, "SetConstraint", "*/Facility/GroundStation1", 'ElevationAngle Min -90.0 Max 90.0 ExcludeIntervals')
    atkConnect(base, "Animate", "*", "Reset")

    # 创建地面站传感器
    atkConnect(base, "New", "/", "Facility/GroundStation1/Sensor Sensor1")
    atkConnect(base, "Define", "*/Facility/GroundStation1/Sensor/Sensor1", "Rectangular 25.1 36.8")
    atkConnect(base, "Point", '*/Facility/GroundStation1/Sensor/Sensor1', 'Fixed Euler 121 180.0 0.0 0.0')
    atkConnect(base, "Graphics", '*/Facility/GroundStation1/Sensor/Sensor1', f'SetColor {color_num}')
    color_num = color_num + 1
    atkConnect(base, "Animate", "*", "Reset")

    # 获取可见性报告
    atkConnect(base, "Report_RM", '*/Facility/GroundStation1/Sensor/Sensor1', 'Style "Access" Type Display AccessObject */Satellite/sat_para TimePeriod "1 Jan 2025 00:00:00.000" "5 Jan 2025 00:00:00.000"')
    atkConnect(base, "Report_RM", '*/Facility/GroundStation1/Sensor/Sensor1', 'Style "Access" Type Display AccessObject */Satellite/sat_tle TimePeriod "1 Jan 2025 00:00:00.000" "5 Jan 2025 00:00:00.000"')

    # 关闭 ATK
    atkClose(base)
