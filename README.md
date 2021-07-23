# create_queries
To use the create_queries(pair) function, the data in pair must be of this shape:

```
{
		'triple_patterns': [ #list of bgp
					 [ #list of queries in each bgp
						{ #one query
					   	  'subject': String,
					   	  'predicate': String, 
					   	  'object': String, 
					   	  'source': 'M1' / 'M2' / 'M1 M2'
						}
					 ]
				   ],
		'name1': String,	#name of the first source   like so: <http://localhost:8890/' + name 1 + '>
		'name2': String		#name of the second source
}
```
