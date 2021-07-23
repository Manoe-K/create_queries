# create_queries
To use the create_queries(pair) function, the data in `pair` must be of this shape:

```
{
	'triple_patterns': [ #list of bgp
				[ #list of queries in each bgp
					{ #one query
						'subject':   String,
					   	'predicate': String, 
					   	'object':    String, 
					   	'source':    String 	#One of those values: 'M1' / 'M2' / 'M1 M2'
					}
				]
			   ],
	'name1': String,	#name of the first source   like so: <http://localhost:8890/' + name 1 + '>
	'name2': String		#name of the second source
}
```
TODO: Add the possibility to read a file / String as input


This tool uses a local endpoint that needs to be setup with virtuoso in order to store rdf datasets.
The datasets name shall be stored in graphs which names are the same as given in the `pair` data (name1 and name2).
The queries created ask two graph everytime, and the datasets that wants to be tested need to be in two different graph.

### Setup
sparqlwrapper needs to be installed
`pip install sparqlwrapper`
