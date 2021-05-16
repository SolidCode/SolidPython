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

module blub(a, b=1) cube([a, 2, 2]);

function scad_points() = [[0,0], [1,0], [0,1]];

// In Python, calling this function without an argument would be an error.
// Leave this here to confirm that this works in OpenSCAD.
function optional_nondefault_arg(arg1) =
  let(s = arg1 ? arg1 : 1) cube([s,s,s]);

echo("This text should appear only when called with include(), not use()");
