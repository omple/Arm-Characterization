#include <Servo.h>
#include <math.h>

// Servo objects
Servo servo1;  // Base joint
Servo servo2;  // Elbow joint

// Pin definitions
const int SERVO1_PIN = 9;
const int SERVO2_PIN = 10;

// Link lengths (adjust to match your physical arm)
const float a1 = 0.075;  // Length of first link
const float a2 = 0.07;  // Length of second link

// Servo angle offsets and direction
const float SERVO1_OFFSET = 90.0;
const float SERVO2_OFFSET = 90.0;
const bool SERVO1_REVERSE = false;
const bool SERVO2_REVERSE = false;

void setup() {
  Serial.begin(9600);

  // Attach servos
  servo1.attach(SERVO1_PIN);
  servo2.attach(SERVO2_PIN);

  // Initialize to home position
  servo1.write(90);
  servo2.write(90);

  Serial.println("\nEnter target position as: x,y");
  Serial.println("Example: 15.5,8.2");
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    // Parse x and y
    int commaIndex = input.indexOf(',');
    if (commaIndex > 0) {
      float x1 = input.substring(0, commaIndex).toFloat();
      float y1 = input.substring(commaIndex + 1).toFloat();

      Serial.println();
      Serial.print("Target: (");
      Serial.print(x1);
      Serial.print(", ");
      Serial.print(y1);
      Serial.println(")");

      // Calculate and move to position
      calculateDirectIK(x1, y1);
    } else {
      Serial.println("Invalid format. Use: x,y");
    }
  }
}

void calculateDirectIK(float x1, float y1) {
  // Calculate a3 = distance from origin to target
  float a3 = sqrt(x1*x1 + y1*y1);

  // Check reachability
  if (a3 > (a1 + a2)) {
    Serial.println("ERROR: Target too far!");
    Serial.print("Max reach: ");
    Serial.println(a1 + a2);
    return;
  }

  // Calculate intermediate terms
  float a1_sq = a1 * a1;
  float a2_sq = a2 * a2;
  float a3_sq = a3 * a3;

  float q1, p1;

  q1 = atan(y1,x1) - arccos(a2_sq - a1_sq - a3_sq, -2 * a1 * a3);
  p1 = atan(y1,x1) + arccos(a2_sq - a1_sq - a3_sq, -2 * a1 * a3);

  // Apply servo offsets and direction
  int servo1_angle = q1 + SERVO1_OFFSET;
  int servo2_angle = p1 + SERVO2_OFFSET;

  if (SERVO1_REVERSE) {
    servo1_angle = 180 - servo1_angle;
  }
  if (SERVO2_REVERSE) {
    servo2_angle = 180 - servo2_angle;
  }

  // Constrain to servo limits
  servo1_angle = constrain(servo1_angle, -20, 80);
  servo2_angle = constrain(servo2_angle, 45, 110);

  Serial.println("\nServo Commands:");
  Serial.print("  Servo1: ");
  Serial.print(servo1_angle);
  Serial.println(" deg");
  Serial.print("  Servo2: ");
  Serial.print(servo2_angle);
  Serial.println(" deg");

  // Move servos
  servo1.write(servo1_angle);
  servo2.write(servo2_angle);

  Serial.println("\n>> Position Reached! <<");
  Serial.println("========================\n");
}
