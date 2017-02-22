year=$1
startmonth=$2
if [ "$3" == "D" ]
then
  path=/dfs/scratch0/viswa/NYT_temp/
else
  path=/lfs/madmax6/0/viswa/LDC2008T19_The-New-York-Times-Annotated-Corpus/data/data2/
fi
port=$4

echo $year
echo $startmonth
echo $path
for i in `seq $startmonth 4 12`; do
  echo $i
  python2.7 analysis/annotate_NYT.py $year $i  --port $port --path $path
done
