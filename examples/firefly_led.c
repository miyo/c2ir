
char led;

void firefly_led(int a, int b)
{
  int i;
  led = 0;
  for(i = 0; i < a; i++) ;
  led = 1;
  for(i = 0; i < b; i++) ;
}

void firefly_led_test(){
  int i;
  for(i = 1; i < 16; i++){
    firefly_led(i, 16-i);
  }
  for(i = 15; i > 0 ; i--){
    firefly_led(i, 16-i);
  }
}
