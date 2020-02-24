from ev3dev2.motor import LargeMotor, MoveSteering, MoveTank, OUTPUT_B, OUTPUT_C

steer_pair = MoveSteering(OUTPUT_B, OUTPUT_C, motor_class=LargeMotor)
def handle_move_forward_cm(cm, speed):
    degrees_to_run = cm / 17.5 * 360
    steer_pair.on_for_degrees(steering=0, speed=speed, degrees=degrees_to_run)

if __name__ == "__main__":
    handle_move_forward_cm(10, 80)