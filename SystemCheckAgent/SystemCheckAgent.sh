#/bin/bash
################################################################################
# SystemCheckAgent.sh
################################################################################
#. ${HOME}/.bash_profile
source ${HOME}/.bash_profile
##-------------------------------------------------------------------------------
## Service Variable
##-------------------------------------------------------------------------------
#

APP_DIR=$(readlink -f $0 |xargs dirname)
TMP_DIR=$APP_DIR/tmp
CONF_DIR=$APP_DIR/conf
DATA_DIR=$APP_DIR/data
DATA_FILE=$DATA_DIR/SystemStatus_$(date +'%Y%m%d_%H')
find $DATA_DIR -mmin +180 -delete
if [ -z "$1" ]; then
	echo ""
	echo "Define your configration file!!"
	echo ""
	echo " Usage: SystemCheckAgent.sh \$CONF_DIR/SystemCheckAgent.conf"
	echo ""
	exit
elif [ ! -e "$1" ]; then
	echo ""
	echo "Configration File is not Exist!"
	echo ""
	exit
else
	source "$1"
fi

for DIR_NAME in $TMP_DIR $DATA_DIR $CONF_DIR
        do
        if [ ! -d $DIR_NAME ]; then
                mkdir -p $DIR_NAME
        fi
done

function FileInodeCheck() {
	t_inode_file=$TMP_DIR/$t_name.inode
	past_inode=$(cat $t_inode_file 2>&1)
	now_inode=$(ls -i $target_file|awk '{print $1}')
	if [ -e "$t_inode_file" -a -n "$past_inode" ]; then
	        if [ "$past_inode" -ne "$now_inode"  ]; then
	                s_offset=1
	                echo $s_offset > $offset_file
	                echo $now_inode > $t_inode_file
	        fi
	else
	        echo $now_inode > $t_inode_file
	fi
}
function GetOffset() {
	local target_file=$1
	t_name=$(echo $target_file|rev|cut -d'/' -f1 |rev)
	t_inode_file=$TMP_DIR/$t_name.inode
	offset_file=$TMP_DIR/$t_name.offset
	if [ ! -e "$offset_file" ]; then
		touch $offset_file
	fi
	FileInodeCheck
	s_offset=$(cat $offset_file)
	e_offset=$(nl $target_file|tail -1|awk '{print $1}')
	if [ -n "$s_offset" ]; then
	        sed -n "${s_offset},${e_offset}p" $target_file
	        echo $((e_offset+1)) > $offset_file
	else
	        s_offset=1
	        sed -n "${s_offset},${e_offset}p" $target_file
	        echo $((e_offset+1)) > $offset_file
	fi
}

function PercentToFloat() {
	local per_pattern="^[0-9]+%"
	local int_pattern="^[0-9]"
	local p_value="$1"
	echo "$p_value" | while read l_value
	do
		if [[ $l_value =~ $per_pattern ]]; then
			echo $l_value | awk -F'%' '{print $1/100 $2}'
		elif [[ $l_value =~ $int_pattern ]]; then
			echo $l_value | awk '{print $1/100 $2}'
		else
			exit
		fi
	done
	
}

function ModeDefine() {
	result=$1
	if [ "$mode" == "file" ]; then
		echo "$result" >> $DATA_FILE
	elif [ "$mode" == "console" ]; then
		echo "$result"
	else
		echo "$result"
	fi
}
function MetricAppend() {
	host=$(hostname)
	event_time=$(date +'%Y%m%d%H%M'00)
	metric_result+=$(awk -v metric_name="$metric_name|" '{print metric_name $0}')
	result=$(echo "$metric_result" |awk -v module="$module_name|" -v host="$host|" -v event_time="$event_time|" '{print module host event_time $0}')
	#echo "$result" >> $DATA_FILE
	#echo "$result"
	ModeDefine "$result"
}
function CheckFsUsage() {
	local metric_name="fs_usage"
	local result="$(df -h -x fuse.gvfs-fuse-daemon -x fuse.glusterfs | awk 'NR>=2 {print $5"|"$6}'|grep -v "$false_fs")"
	PercentToFloat "$result"|MetricAppend
}
function CheckInodeUsage() {
	local metric_name="inode_usage"
	local result="$(df -i -x fuse.gvfs-fuse-daemon -x fuse.glusterfs | awk 'NR>=2 {print $5"|"$6}'|grep -v "$false_fs")"
	PercentToFloat "$result"|MetricAppend
}
function CheckDiskStatus() {
	local metric_name="disk_status"
	local disk_list=$(df -i -x fuse.gvfs-fuse-daemon -x fuse.glusterfs | awk 'NR>=2 {print $6}'|grep -v "$false_fs")
	echo "$disk_list" | while read DISK; do
                ### 0: OK 1: NOK
				IO_Check=$(ls $DISK 2>&1 > /dev/null)
				if [ $? -eq 0 ]; then
					RW_Check=$(/bin/findmnt -o OPTIONS $DISK |tail -1|awk -F',' '{print $1}' )
	                if [ ${RW_Check} == "rw" ]; then
						echo "0|$DISK" | MetricAppend
	                else
                        echo "1|$DISK" | MetricAppend
    	            fi
				else
					echo "1|$DISK" | MetricAppend
				fi
	done
}
function CheckMemoryStatus() {
	local metric_name="memory_ce_cnt"
	local target_file=/var/log/messages
	if [ -r $target_file ]; then
		GetOffset $target_file |grep 'CE memory.*.error'|wc -l|MetricAppend
	fi
}
function CheckZombie() {
	local metric_name="zombie_cnt"
	ps -ef | grep '<defunct>' | grep -v grep | grep -v sendmail | wc -l|MetricAppend
}
CheckFsUsage
CheckInodeUsage	
CheckDiskStatus
CheckZombie
CheckMemoryStatus
