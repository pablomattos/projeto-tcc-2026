#include <Wire.h>
#include <math.h>

#define device 0x0D 

#define controlms byte(0x80)
#define controlls byte(0x81)

#define startfreqmms byte(0x82)
#define startfreqms byte(0x83)
#define startfreqls byte(0x84)

#define freqincmms byte(0x85)
#define freqincms byte(0x86)
#define freqincls byte(0x87)

#define numincsms byte(0x88)
#define numincsls byte(0x89)

#define numcyms byte(0x8A)
#define numcyls byte(0x8B)

#define sstatus byte(0x8F)

#define tempms byte(0x92)
#define templs byte(0x93)

#define realms byte(0x94)
#define realls byte(0x95)

#define imms byte(0x96)
#define imls byte(0x97)

//Pines multiplexores
const int EN1 = 52;
const int muxS0 = 50;
const int muxS1 = 48;
const int muxS2 = 46;
const int muxS3 = 44;

const int EN2 = 42;
const int muxW0 = 40;
const int muxW1 = 38;
const int muxW2 = 36;
const int muxW3 = 34;

const int EN3 = 32;
const int muxY0 = 30;
const int muxY1 = 28;
const int muxY2 = 26;
const int muxY3 = 24;

const int EN4 = 53;
const int muxZ0 = 51;
const int muxZ1 = 49;
const int muxZ2 = 47;
const int muxZ3 = 45;


int muxIC2(byte channel1)
{
  digitalWrite(muxS0, bitRead(channel1, 0));
  digitalWrite(muxS1, bitRead(channel1, 1));
  digitalWrite(muxS2, bitRead(channel1, 2));
  digitalWrite(muxS3, bitRead(channel1, 3));
  
}

int muxIC3(byte channel2)
{
  digitalWrite(muxW0, bitRead(channel2, 0));
  digitalWrite(muxW1, bitRead(channel2, 1));
  digitalWrite(muxW2, bitRead(channel2, 2));
  digitalWrite(muxW3, bitRead(channel2, 3));
}

int muxIC4(byte channel3)
{
  digitalWrite(muxY0, bitRead(channel3, 0));
  digitalWrite(muxY1, bitRead(channel3, 1));
  digitalWrite(muxY2, bitRead(channel3, 2));
  digitalWrite(muxY3, bitRead(channel3, 3));
}

int muxIC5(byte channel4)
{
  digitalWrite(muxZ0, bitRead(channel4, 0));
  digitalWrite(muxZ1, bitRead(channel4, 1));
  digitalWrite(muxZ2, bitRead(channel4, 2));
  digitalWrite(muxZ3, bitRead(channel4, 3));
}


void setup() {
  // put your setup code here, to run once:
  //I2C
  Wire.begin(); 
  Serial.begin(9600);
  //multiplexers
  pinMode(muxS0, OUTPUT);
  pinMode(muxS1, OUTPUT);
  pinMode(muxS2, OUTPUT);
  pinMode(muxS3, OUTPUT);
  pinMode(EN1, OUTPUT);
  digitalWrite(EN1, LOW);
  pinMode(muxW0, OUTPUT);
  pinMode(muxW1, OUTPUT);
  pinMode(muxW2, OUTPUT);
  pinMode(muxW3, OUTPUT);
  pinMode(EN2, OUTPUT);
  digitalWrite(EN2, LOW);
  pinMode(muxY0, OUTPUT);
  pinMode(muxY1, OUTPUT);
  pinMode(muxY2, OUTPUT);
  pinMode(muxY3, OUTPUT);
  pinMode(EN3, OUTPUT);
  digitalWrite(EN3, LOW);
  pinMode(muxZ0, OUTPUT);
  pinMode(muxZ1, OUTPUT);
  pinMode(muxZ2, OUTPUT);
  pinMode(muxZ3, OUTPUT);
  pinMode(EN4, OUTPUT);
  digitalWrite(EN4, LOW);
}

byte adreadregister(byte address){

  Wire.beginTransmission(device); 
  Wire.write(0xB0); 
  Wire.write(address); 
  Wire.endTransmission(); 
 
  Wire.requestFrom(device, 1);  
  byte val=0x00;
  if(1 <= Wire.available()){
    val = Wire.read();
  }
  return val;
}

byte adwriteregister(byte address, byte val){

  Wire.beginTransmission(device); 
  Wire.write(address); 
  Wire.write(val); 
  Wire.endTransmission();
}

void adreset(){
  byte auxreg=adreadregister(controlls);
  auxreg = 0x10; 
  adwriteregister(controlls,byte(auxreg)); 
}

void adstandby(){
  byte auxreg=adreadregister(controlms);
  auxreg = 0xB0; 
  adwriteregister(controlms,byte(auxreg));  
}

void adprogfreqsweep(){
  byte dat1=adreadregister(startfreqmms);
  dat1=0x19;
  adwriteregister(startfreqmms,byte(dat1));
  byte dat2=adreadregister(startfreqms);
  dat2=0x99;
  adwriteregister(startfreqms,byte(dat2));
  byte dat3=adreadregister(startfreqls);
  dat3=0x99;
  adwriteregister(startfreqls,byte(dat3)); 
}

void adsetgain(){
  byte auxreg=adreadregister(controlms);
  auxreg = 0x01;
  adwriteregister(controlms,byte(auxreg));  
}

void adsetamp(){
  byte auxreg=adreadregister(controlms);
  auxreg = 0x06; 
  adwriteregister(controlms,byte(auxreg));
}

void adinitfreq(){
  byte auxreg = adreadregister(controlms);
  auxreg = 0x10;
  adwriteregister(controlms,byte(auxreg));
}

void adsweep(){
  byte auxreg = adreadregister(controlms);
  auxreg = 0x20;
  adwriteregister(controlms,byte(auxreg));
}

void adrepfreq(){
  byte auxreg = adreadregister(controlms);
  auxreg = 0x40; 
  adwriteregister(controlms,byte(auxreg));
}

int i, j;
byte h1, h2, d1, d2;
int real, img;
float auxf1,auxf2, re, im;
byte a=0; 
byte b=1;
byte c=2; 
byte d=3;
byte e=4;
byte f=5;
byte g=6;
byte h=7;
byte s=8;
byte t=9;
byte k=10;
byte l=11;
byte m=12;
byte n=13;
byte o=14;
byte p=15;
int measure[8];


void loop(){
  adprogfreqsweep();
  adstandby();  
  adreset();
  adinitfreq();
  delay(10);
  adsweep();
  while(!(adreadregister(sstatus) &0x04)){
   for(i=0; i<8; i++){
    if(i==0){
     muxIC2(c);
     muxIC3(a);
    }
    else if(i==1){
     muxIC2(d);
     muxIC3(a);
    }
    else if(i==2){
     muxIC2(d);
     muxIC3(b);
    }
    else if(i==3){
     muxIC2(e);
     muxIC3(b);
    }
    else if(i==4){
     muxIC2(e);
     muxIC3(c);
    }
    else if(i==5){
     muxIC2(f);
     muxIC3(c);
    }
    else if(i==6){
     muxIC2(f);
     muxIC3(d);
    }
    else if(i==7){
     muxIC2(c);
     muxIC3(d);
    }
    for(j=0; j<8; j++){
     if(j==0){
      muxIC4(b);
      muxIC5(a);
     }
     else if(j==1){
      muxIC4(c);
      muxIC5(a);
     }
     else if(j==2){
      muxIC4(c);
      muxIC5(s);
     }
     else if(j==3){
      muxIC4(d);
      muxIC5(s);
     }
     else if(j==4){
      muxIC4(d);
      muxIC5(t);
     }
     else if(j==5){
      muxIC4(e);
      muxIC5(t);
     }
     else if(j==6){
      muxIC4(e);
      muxIC5(k);
     }
     else if(j==7){
      muxIC4(b);
      muxIC5(k);
     }
     while(!(adreadregister(sstatus)&0x02)); 
                  
     //real 
     h1=adreadregister(realms);    
     d1=adreadregister(realls);
     real=h1;    
     real=real<<8;
     real=real|d1;
     re=abs(real);
     auxf1=re*re;

     //imaginary
     h2=adreadregister(imms);      
     d2=adreadregister(imls);
     img=h2;      
     img=img<<8;
     img=img|d2;
     im=abs(img);
     auxf2=im*im;
     
     
     float imp = (9.782e-1*(sqrt(auxf1+auxf2)))-2.3102e3;
     int r=abs(imp);   
     //float deg = (atan(im/re))*(180/3.1416);
     //float phase = (-0.0192*deg)+0.853;   
     //measure[j]=r;
     Serial.print(r);         
     //Serial.print("  ");
     //Serial.print("\r\r");
     //Serial.print(phase); 
     Serial.print("\n");       
     adrepfreq();   
    }
//    for(int y=0;y<8;y++){
//     Serial.println(measure[y]);
//    }
    //Serial.print("\n");
   }
   i=0;
   j=0;
   //Serial.print(";");
   Serial.print("\n\n\n");
  }
} 
