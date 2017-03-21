
int c;

void pwm_out(int a, int b)
{
  int i;
  c = 0;
  for(i = 0; i < a; i++) ;
  c = 1;
  for(i = 0; i < b; i++) ;
}

void pwm_test(){
  int i;
  for(i = 1; i < 16; i++){
    pwm_out(i, 16-i);
  }
  for(i = 15; i > 0 ; i--){
    pwm_out(i, 16-i);
  }
}
