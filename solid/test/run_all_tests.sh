for i in `ls ./test_*.py`;
do 
echo $i;
python $i;
done
