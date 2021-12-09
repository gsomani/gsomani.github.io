#include<cstring>
#include<iostream>
#include<algorithm>
#include<utility>
#include<vector>

using namespace std;

vector<int> convert_to_vector(string s)
{
	string::iterator it;
	vector<int> num;
	for(it = s.end()-1; it >= s.begin(); it--)
		num.push_back(*it - '0'); 
	return num;
}

pair<vector<int>,vector<int>> generate_vectors(pair<string,string> s)  
{
	pair<vector<int>,vector<int>> num; 
	num.first = convert_to_vector(s.first);
	num.second = convert_to_vector(s.second); 
	length = max(num.first.size(),num.second.size());
	num.first.resize(length);
	num.second.resize(length);
	return num;
}

pair<vector<int>,vector<int>> split(string s, int pos)
{
    pair<vector<int>,vector<int>> num;
    num.first = { start, s.length()-pos };
    num.second = { s.substr(s.length()-pos,pos} ;
    return num;
}

vector<int> operator+(vector<int> &a, vector<int> &b)
{
vector<int> result(num.size()+1);


for(int



}

string karatsuba(string a, string b)
{ 
  int m,split_pos,z0,z1,z2; 
  m = min(a.length(), b.length());
  split_pos = ceil(m / 2);
  
  pair<vector<int>,vector<int>> num1,num2;
  
  num1 = split(a,split_pos);
  num2 = split(b,split_pos);

  z0 = karatsuba(num1.second,num2.second);
  z2 = karatsuba(num1.first,num2.first); 
  z1 = karatsuba( + high1, low2 + high2)

}

int main()
{

}
