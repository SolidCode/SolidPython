external_var = false;
module steps(howmany=3){
    union(){
        for (i=[0:howmany-1]){
            translate( [i*10,0,0]){
                cube( [10,10,(i+1)*10]);
            }
        }
    }
    
    if (external_var){
        echo( "external_var passed in as true");
    }
}

echo("This text should appear only when called with include(), not use()");