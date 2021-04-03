const int INPUT_PINS[3] = {A0, A1, A2};
const int currentSensors = 3;
int sensors[3][5] = {0, 0, 0};
int sensorsMin[3] = {260, 260, 260};
int sensorsMax[3] = {620, 620, 620};
int sensorsStart[3] = {1000, 1000, 1000};
int sensorsEnd[3] = {0, 0, 0};
long sensorsRelayDuration[3] = {1000, 1000, 1000};

char b[12];
int readIndex = 0;

const int RELAY_PINS[4] = {6, 5, 4, 3};
long relayTimers[4] = {0, 0, 0, 0};

long deltaTime;
unsigned long oldMillis;

long relayCooldown = 5 * 60 * 1000L; //set default relay cooldown value to 5 minutes
long currentCooldown;

bool autoLog;
long logDelay = 60 * 1000L; // read every sixty seconds
long nextLogStep = 0L;

void CheckForLogValuesRequest(char b[12])
{
  if (b[0] == 's' && b[1] == 'r')
  {
    LogSensorValues();
  }
}

void CheckForValueSetter(char b[12])
{
  if (b[0] == 'v')
  {
    char sensorNo[2] = {b[1], '\0'};
    int sensorIndex = atoi(sensorNo);
    char valueNo[6] = {b[3], b[4], b[5], b[6], b[7], '\0'};
    long newValue = atol(valueNo);

    Serial.print("Setting ");

    if (b[2] == 'm')
    {
      sensorsMin[sensorIndex] = newValue;
      Serial.print("full humidity value for sensor ");
    }
    else if (b[2] == 'M')
    {
      sensorsMax[sensorIndex] = newValue;
      Serial.print("zero humidity value for sensor ");
    }
    else if (b[2] == 's')
    {
      sensorsStart[sensorIndex] = newValue;
      Serial.print("pump start value for sensor ");
    }
    else if (b[2] == 'e')
    {
      sensorsEnd[sensorIndex] = newValue;
      Serial.print("pump stop value for sensor ");
    }
    else if (b[2] == 'r')
    {
      sensorsRelayDuration[sensorIndex] = newValue;
      Serial.print("pumping duration for sensor ");
    }
    Serial.print(sensorIndex);
    Serial.print(" to ");
    Serial.println(newValue);
    Serial.flush();
  }
  else if (b[0] == 'l' && b[1] == 'o' && b[2] == 'g')
  {
    char valueNo[8] = {b[3], b[4], b[5], b[6], b[7], b[8], b[9], '\0'};
    long newValue = atol(valueNo);
    logDelay = newValue;
    Serial.print("Setting logging timer to ");
    Serial.println(newValue);
    Serial.flush();
  }
  else if (b[0] == 'r' && b[1] == 'e' && b[2] == 'l')
  {
    char valueNo[8] = {b[3], b[4], b[5], b[6], b[7], b[8], b[9], '\0'};
    long newValue = atol(valueNo);
    relayCooldown = newValue;
    Serial.print("Setting relay cooldown value to ");
    Serial.println(newValue);
    Serial.flush();
  }
}

void CheckForMockSensorValue(char b[12])
{
  if (b[0] == 's' && b[2] == 'v')
  {
    char sensorNo[2] = {b[1], '\0'};
    int sensorIndex = atoi(sensorNo);
    char valueNo[5] = {b[3], b[4], b[5], b[6], '\0'};
    int newValue = atoi(valueNo);

    SetSensorHistory(sensorIndex, newValue);

    Serial.print("Setting mock value for sensor ");
    Serial.print(sensorIndex);
    Serial.print(" to ");
    Serial.println(newValue);
    Serial.flush();
  }
}

void StartRelay(int relay, long onDuration)
{
  relayTimers[relay] = onDuration;
  digitalWrite(RELAY_PINS[relay], LOW);

  currentCooldown = relayCooldown;

  Serial.print("Opening relay ");
  Serial.print(relay);
  Serial.print(" for ");
  Serial.print(onDuration);
  Serial.println("ms");
  Serial.flush();
}

void StopRelay(int relay)
{
  digitalWrite(RELAY_PINS[relay], HIGH);

  // Serial.print("Closing relay ");
  // Serial.println(relay);
  // Serial.flush();
}

void CheckForMockRelayStart(char b[12])
{
  if (b[0] == 'r' && b[2] == 'd')
  {
    char relayNo[2] = {b[1], '\0'};
    int relay = atoi(relayNo);
    char durationNo[6] = {b[3], b[4], b[5], b[6], b[7], '\0'};
    long onDuration = atol(durationNo);

    StartRelay(relay, onDuration);
  }
}

void PrintCurrentSettings()
{
  Serial.print("{ ");
  for (int i=0; i<currentSensors; i++)
  {
    Serial.print(" \"sensor");
    Serial.print(i);
    Serial.print("\": ");
    Serial.print(" { ");
    Serial.print(" \"zero_humidity\": ");
    Serial.print(sensorsMax[i]);
    Serial.print(", ");
    Serial.print(" \"full_humidity\": ");
    Serial.print(sensorsMin[i]);
    Serial.print(", ");
    Serial.print(" \"relay_start\": ");
    Serial.print(sensorsStart[i]);
    Serial.print(", ");
    Serial.print(" \"relay_duration\": ");
    Serial.print(sensorsRelayDuration[i]);
    Serial.print("}");
    if (i<currentSensors-1)
      Serial.print(", ");
  }
  Serial.print(", \"log_delay\": ");
  Serial.print(logDelay);
  Serial.print(", \"relay_cooldown\": ");
  Serial.print(relayCooldown);
  Serial.println("}");
}

void CheckForStatusReportRequest(char b[12])
{
  if (b[0] == 's' && b[1] == 't' && b[2] == 'a' && b[3] == 't')
  {
    PrintCurrentSettings();
  }
}

bool SerialReadLoop()
{
  if (Serial.available())
  {
    b[readIndex] = Serial.read();
    readIndex++;
    if (b[readIndex - 1] == '\0')
    {
      return false;
    }
    if (readIndex == 11 || b[readIndex - 1] == '\n' || b[readIndex - 1] == '\r')
    {
      CheckForLogValuesRequest(b);
      CheckForValueSetter(b);
      CheckForMockSensorValue(b);
      CheckForMockRelayStart(b);
      CheckForStatusReportRequest(b);
      readIndex = 0;
    }
  }
  return true;
}

void setup()
{
  // Initialize pins
  for (int i=0; i<3; i++)
  {
    pinMode(INPUT_PINS[i], INPUT);
  }
  for (int i=0; i<4; i++)
  {
    pinMode(RELAY_PINS[i], OUTPUT); 
    digitalWrite(RELAY_PINS[i], HIGH);
  }

  // Initialzie serial connection
  Serial.begin(9600);
  while (!Serial) 
  {
    ; // wait for serial port to connect. Needed for native USB
  }

  // Send ready signal to computer
  Serial.println("Ready");
  Serial.flush();

  autoLog = false;

  // Initialize from stored values
  while (true)
  {
    if (SerialReadLoop() == false)
    {
      Serial.println("End of config file reached!");
      Serial.flush();
      autoLog = false;
      break;
    }
  
    if (millis() > (long)10000) // timeout in 10 seconds
    {
      Serial.println("Timeout on starting values. Initializing default values and auto logging flag.");
      Serial.flush();
      autoLog = true;
      break;
    }
  } 

  // Initialize global variables
  oldMillis = millis();
  nextLogStep = 0;
  currentCooldown = relayCooldown;
}

long getDeltaTime()
{
  long returnValue = millis() - oldMillis;
  oldMillis = millis();
  return returnValue;
}

float ConvertToPercent(int sensorValue, int sensorMin, int sensorMax)
{
  float x = (float)(sensorValue - sensorMin) / (float)(sensorMax - sensorMin);
  return (float)(1.0 - x) * 100.0; // inversion happens here (sensorMin is 100% sensorMax is 0%)
}

float AverageValue(int index)
{
  int sum = 0;
  for (int i=0; i<5; i++)
  {
    sum += sensors[index][i];
  }
  return (float)sum / (float)5;
}

void SetSensorHistory(int i, int newValue)
{
      for(int j=4; j>0; j--)
      {
        sensors[i][j] = sensors[i][j-1];
      }
      sensors[i][0] = newValue;
}

void TestRelayStartCondition()
{
  // check if relay was started in the last <relayCooldown> minutes
  if (currentCooldown < 0) 
  {
    for(int i=0; i<currentSensors; i++)
    {
      if (AverageValue(i) > sensorsStart[i])
      {
        StartRelay(i, sensorsRelayDuration[i]);
      }
    }
  }
}

void LogSensorValues()
{
  for(int i=0; i<currentSensors; i++)
  {
    SetSensorHistory(i, analogRead(INPUT_PINS[i]));
    if (i>0)
      Serial.print(",");
    Serial.print(constrain(ConvertToPercent(sensors[i][0], sensorsMin[i], sensorsMax[i]), 0.00, 100.00));
    // Serial.print(sensors[i][0]);
  }
  Serial.println("");
  Serial.flush();

  TestRelayStartCondition();
}

void LoggerCountdown()
{
  if (nextLogStep <= 0)
  {
    LogSensorValues();
    nextLogStep += logDelay;
  }
  nextLogStep -= deltaTime;
}

void RelayCommandLoop()
{
  for (int i = 0; i < 4; i++)
  {
    if (relayTimers[i] > 0)
    {
      relayTimers[i] -= deltaTime;
      if (relayTimers[i] <= 0)
      {
        StopRelay(i);
      }
    }
  }
}

void RelayCooldownLoop()
{
  if (currentCooldown >= 0)
  {
    currentCooldown -= deltaTime;
  }
}

void loop()
{
  deltaTime = getDeltaTime();
  if (autoLog == true)
  {
    LoggerCountdown();
  }
  SerialReadLoop();
  RelayCommandLoop();
  RelayCooldownLoop();
}
