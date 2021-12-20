function generate_sequence(){
var sutra = ["अइउण्","ऋऌक्","एओङ्","ऐऔच्","हयवरट्","लण्","ञमङणनम्","झभञ्","घढधष्","जबगडदश्","खफछठथचटतव्","कपय्","शषसर्","हल्"];
var i,j,k;
var index_str = "";
var pratyahar_calc = "";

var duplicate_h = new Array(2);

var pratyahar_count = 0;
var pratyahar_with_nth_it = new Array(sutra.length);

for(i = 0, k=0 ; i < sutra.length ; i++)
{
	for(j = 0; j < sutra[i].length - 2; j++,k++)
	{
		index_str += "$a_{" + k + '},$ ';	
		if(sutra[i][j]=='ह')
				
	}
	
	index_str += "$b_{" + i + '}$, <br> ';

	pratyahar_with_nth_it[i] = (k-1);

	pratyahar_count += (k - 1); 

}

for(i = 0 ; i < sutra.length - 1; i++)
	pratyahar_calc += pratyahar_with_nth_it[i] + ' + ';

pratyahar_calc += pratyahar_with_nth_it[i] + ' = ' +  pratyahar_count;

return [index_str,pratyahar_calc];

}

function update_div(div){

	var tag_sequence = document.getElementById(div[0]);

	var string_list;

	string_list = generate_sequence();
		
	tag_sequence.innerHTML = string_list[0];

	tag.appendChild(document.createTextNode(string_list[1]));

}
