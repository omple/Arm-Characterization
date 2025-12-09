#include <Servo.h>
#include <math.h>

// Servo objects
Servo servo1;  // Base joint
Servo servo2;  // Elbow joint

// Pin definitions
const int SERVO1_PIN = 7;
const int SERVO2_PIN = 8;

// Link lengths (adjust to match your physical arm)
const float a1 = 0.0922;  // Length of first link
const float a2 = 0.08024;  // Length of second link
const float o = 0.025;

// Servo angle offsets and direction
const float SERVO1_OFFSET = 90.0;
const float SERVO2_OFFSET = 90.0;
const float SERVO1_REVERSE = 1.0;
const float SERVO2_REVERSE = 1.0;
const int SERVO_MIN = -90;
const int SERVO_MAX = 180;

void setup() {
  Serial.begin(9600);

  // Attach servos
  servo1.attach(SERVO1_PIN);
  servo2.attach(SERVO2_PIN);

  // Initialize to home position
  servo1.write(90);
  servo2.write(90);
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
      Serial.println("ERROR: Invalid format. Use: x,y");
    }
  }
}

float radiansToDegrees(float radians) {
  return radians * (180.0 / PI);
}


bool solveAnglesWorld(float xW, float yW,
                      float &p1_deg,
                      float &q1_deg)
{
  float x1 = xW - o;
  float y1 = yW;
  float d1 = sqrtf(x1*x1 + y1*y1);

  float x2 = xW;
  float y2 = yW - o;
  float d2 = sqrtf(x2*x2 + y2*y2);

  if (d1 > (a1 + a2) || d1 < fabsf(a1 - a2)) return false;
  if (d2 > (a1 + a2) || d2 < fabsf(a1 - a2)) return false;

  float t1_q = (a2*a2 - a1*a1 - d1*d1) / (-2.0f * a1 * d1);

  t1_q = constrain(t1_q, -1.0f, 1.0f);

  float atan_yx_q = atan2f(y1, x1);

  float q1 = atan_yx_q - acosf(t1_q);

  float t1_p = (a2*a2 - a1*a1 - d2*d2) / (-2.0f * a1 * d2);

  t1_p = constrain(t1_p, -1.0f, 1.0f);

  float atan_yx_p = atan2f(y2, x2);

  float p1 = atan_yx_p + acosf(t1_p);

  p1_deg = radiansToDegrees(p1);
  q1_deg = radiansToDegrees(q1);
  return true;
}

void calculateDirectIK(float x1, float y1) {
  // Calculate a3 = distance from origin to target
  float p1; 
  float q1;

  if (!solveAnglesWorld(x1, y1, p1, q1)) {
    Serial.println(">> ERROR: Target Unreachable! <<\n");
    return;
  }

  int sP1 = (int)lroundf(SERVO1_REVERSE * p1 + SERVO1_OFFSET);
  int sQ1 = (int)lroundf(SERVO2_REVERSE * q1 + SERVO2_OFFSET);

  sP1 = constrain(sP1, SERVO_MIN, SERVO_MAX);
  sQ1 = constrain(sQ1, SERVO_MIN, SERVO_MAX);

  /*
  Serial.println("\nServo Commands:");
  Serial.print("  Servo1: ");
  Serial.print(sP1);
  Serial.println(" deg");
  Serial.print("  Servo2: ");
  Serial.print(sQ1);
  Serial.println(" deg");
  */

  // Move servos
  servo1.write(sP1);
  servo2.write(sQ1);

  Serial.println("\n>> Position Reached! <<");
  //Serial.println("========================\n");
}
