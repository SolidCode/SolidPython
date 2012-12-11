module steps( howmany=3){
    union(){
        for (i=[0:howmany-1]){
            translate( [i,0,0]){
                cube( [1,1,i+1]);
            }
        }
    }
}
