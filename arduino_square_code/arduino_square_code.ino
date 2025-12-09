#include <Servo.h>
#include <math.h>
#include <ctype.h>

// ============= ARM GEOMETRY (mm) =============
const float a1 = 92.2f;    // first link length
const float a2 = 80.24f;   // second link length
const float O  = 25.0f;    // offset o (mm)

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

static inline float rad2deg(float r){ return r * (180.0f / M_PI); }

// ============= SERVO SETUP ====================
const int PIN_P1 = 7;
const int PIN_Q1 = 8;

const int   DIR_P1 = +1;
const int   DIR_Q1 = +1;
const float OFF_P1 = 0.0f;
const float OFF_Q1 = 0.0f;

const int SERVO_MIN = 0;
const int SERVO_MAX = 180;

Servo servoP1;
Servo servoQ1;

// --------------------------------------------------
// Inverse Kinematics Solver
// --------------------------------------------------
bool solveAnglesWorld(float xW, float yW,
                      float &p1_deg,
                      float &q1_deg)
{
  float x1 = xW - O;
  float y1 = yW;
  float d1 = sqrtf(x1*x1 + y1*y1);

  float x2 = xW;
  float y2 = yW - O;
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

  p1_deg = rad2deg(p1);
  q1_deg = rad2deg(q1);
  return true;
}

// --------------------------------------------------
// Move servos
// --------------------------------------------------
void moveBases(float p1_deg, float q1_deg)
{
  int sP1 = (int)lroundf(DIR_P1 * p1_deg + OFF_P1);
  int sQ1 = (int)lroundf(DIR_Q1 * q1_deg + OFF_Q1);

  sP1 = constrain(sP1, SERVO_MIN, SERVO_MAX);
  sQ1 = constrain(sQ1, SERVO_MIN, SERVO_MAX);

  servoP1.write(sP1);
  servoQ1.write(sQ1);

  Serial.print("Servos -> p1 = ");
  Serial.print(sP1);
  Serial.print("°, q1 = ");
  Serial.println(sQ1);
}

// --------------------------------------------------
// Move to ONE POINT (P command)
// --------------------------------------------------
void runOnePoint(float xW, float yW)
{
  Serial.print("Target (");
  Serial.print(xW);
  Serial.print(", ");
  Serial.print(yW);
  Serial.println(")");

  float p1, p2, q1, q2;
  if (!solveAnglesWorld(xW, yW, p1, p2, q1, q2)) {
    Serial.println("  -> Unreachable");
    return;
  }

  moveBases(p1, q1);
  Serial.println("Move complete.\n");
}

// --------------------------------------------------
// OLD 3-POSITION SEQUENCE (Q command)
// --------------------------------------------------
void runSequence() {
  const float targets[4][2] = {
    {120.0f, 105.0f},
    {137.0f, 126.0f},
    {137.0f, 54.0f},
    {93.0f, 126.0f}
  };

  for (int i = 0; i < 4; i++) {
    float p1,p2,q1,q2;
    if (solveAnglesWorld(targets[i][0], targets[i][1], p1,p2,q1,q2))
      moveBases(p1, q1);

    delay(200);
  }

  Serial.println("Sequence complete.\n");
}

// --------------------------------------------------
// PARAMETRIC SQUARE (S command)
// Coordinates:
//   Bottom-right = (137, 100)
//   Top-right    = (137, 126)
//   Bottom-left  = (111, 100)
//   Top-left     = (111, 126)
// --------------------------------------------------
void runSquare_RightDefined(float T_total_ms)
{
  const float BR_x = 137.0f, BR_y = 100.0f;
  const float TR_x = 137.0f, TR_y = 126.0f;
  const float BL_x = 111.0f, BL_y = 100.0f;
  const float TL_x = 111.0f, TL_y = 126.0f;

  unsigned long t0 = millis();
  float seg = T_total_ms / 4.0f;

  Serial.println("Starting parametric square...");

  while (millis() - t0 < T_total_ms) {
    float t = millis() - t0;
    float xW, yW;

    if (t < seg) {
      float u = t / seg;
      xW = BR_x;
      yW = BR_y + u * (TR_y - BR_y);

    } else if (t < 2*seg) {
      float u = (t - seg) / seg;
      xW = TR_x + u * (TL_x - TR_x);
      yW = TR_y;

    } else if (t < 3*seg) {
      float u = (t - 2*seg) / seg;
      xW = TL_x;
      yW = TR_y - u * (TR_y - BR_y);

    } else {
      float u = (t - 3*seg) / seg;
      xW = BL_x + u * (BR_x - BL_x);
      yW = BL_y;
    }

    float p1,p2,q1,q2;
    if (solveAnglesWorld(xW,yW,p1,p2,q1,q2))
      moveBases(p1, q1);

    Serial.print("t=");
    Serial.print(t);
    Serial.print("  x=");
    Serial.print(xW);
    Serial.print("  y=");
    Serial.println(yW);

    delay(10); // 100 Hz
  }

  Serial.println("Square complete.\n");
}

// --------------------------------------------------
// Prompt
// --------------------------------------------------
void printPrompt() {
  Serial.println("\nCommands:");
  Serial.println("  P x y  ");
  Serial.println("  Q      3 pt");
  Serial.println("  S      square");
}

// --------------------------------------------------
// Setup
// --------------------------------------------------
void setup() {
  Serial.begin(115200);
  servoP1.attach(PIN_P1);
  servoQ1.attach(PIN_Q1);
  delay(200);
  printPrompt();
}

// --------------------------------------------------
// Loop
// --------------------------------------------------
void loop() {

  if (!Serial.available()) return;

  while (Serial.available() && isspace(Serial.peek())) Serial.read();
  if (!Serial.peek()) return;

  char mode = Serial.peek();

  // ------ P COMMAND ------
  if (mode == 'P' || mode == 'p') {
    Serial.read();
    float xW = Serial.parseFloat();
    float yW = Serial.parseFloat();
    runOnePoint(xW, yW);
    printPrompt();
    return;
  }

  // ------ Q COMMAND ------
  if (mode == 'Q' || mode == 'q') {
    Serial.read();
    runSequence();
    printPrompt();
    return;
  }

  // ------ S COMMAND ------
  if (mode == 'S' || mode == 's') {
    Serial.read();
    runSquare_RightDefined(5000.0f); // 5-second square
    printPrompt();
    return;
  }

  Serial.read(); // ignore unknown input
}
