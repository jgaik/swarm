#define BUFFERSIZE 32

void setValues(String newValues) {

}

void readData() {
  bool bReadMode = false;
  char cDataNew[BUFFERSIZE];
  char cDataStart = '{';
  char cDataEnd = '}';
  int indx = 0;
  while (Serial.available() > 0) {
    char cRead = Serial.read();
    if (bReadMode) {
      if (cRead != cDataEnd) {
        cDataNew[indx] = cRead;
        indx++;
      } else {
        cDataNew[indx] = '\0';
        break;
      }
    } else if (cRead == cDataStart) {
      bReadMode = true;
    }
  }
  setValues(String(cDataNew));
}

void setup() {
  Serial.begin(9600);
}
 
void loop() {
}