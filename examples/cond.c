
int if_tset(int c, int a, int b){
  if(c == 0){
    return a;
  }else{
    return b;
  }
}

int switch_test(int x, int a, int b, int c, int d, int z){
  int ret;
  switch(x){
  case 0: ret = a; break;
  case 1: ret = b; break;
  case 2: ret = c; break;
  case 3: ret = d; break;
  case 4:
  default:
    return z;
  }
  return ret;
}

int for_test(int c, int a){
  int i;
  int sum = 0;
  for(i = 0; i < c; i++){
    sum += a;
  }
  return sum;
}

