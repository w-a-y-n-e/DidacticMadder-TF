if [[ $1 == 'A' ]]
then
	echo "$#"
	echo "Arguments"
	if [[ "$#" -eq 4 ]]
	then
		#$2 = host, $3 =from $4 = to
		iptables -I FORWARD 1 -o virbr0 -d $2 -j ACCEPT
		#sudo firewall-cmd --add-port=$3/tcp
		iptables -t nat -I PREROUTING 1 -p tcp --dport $3 -j DNAT --to $2:$4
		#firewall-cmd --add-forward-port=port=$3:proto=tcp:toport=$4:toaddr=$2
		#sudo firewall-cmd --add-masquerade
	elif [[ "$#" -eq 2 ]]
	then
		echo "TRYING TO ADD LOCAL PORT"
		#2 = to
		firewall-cmd --add-port=$2/tcp
		#iptables -I INPUT 1 -p tcp --dport $2 -j ACCEPT
		#iptables -I OUTPUT 1 -p tcp --sport $2 -j ACCEPT
	fi
elif [[ $1 == 'D' ]]
then
	if [[ "$#" -eq 4 ]]
	then
		iptables -D FORWARD -o virbr0 -d $2 -j ACCEPT
		iptables -t nat -D PREROUTING -p tcp --dport $3 -j DNAT --to $2:$4
		#firewall-cmd --remove-port=$3/tcp
		#firewall-cmd --remove-forward-port=port=$3:proto=tcp:toport=$4:toaddr=$2
	elif [[ "$#" -eq 2 ]]
	then
		firewall-cmd --remove-port=$2/tcp
		#iptables -D INPUT -p tcp --dport $2 -j ACCEPT
		#iptables -D OUTPUT -p tcp --sport $2 -j ACCEPT
	fi
elif [[ "$#" -ne 4 ]]
then
	echo "Usage: A/D, NAT'ed address, port to forward, destination port"
fi
