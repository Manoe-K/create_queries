from SPARQLWrapper import SPARQLWrapper, JSON


def triple_pattern_to_sparql(pattern):
    if pattern['predicate'] == 'a':
        return pattern['subject'] + ' ' + pattern['predicate'] + ' <' + pattern['object'] + '>' + '.'
    elif pattern['predicate'] == 'rdf:type':
        return pattern['subject'] + ' ' + pattern['predicate'] + ' <' + pattern['object'] + '>' + '.'
    else:
        return pattern['subject'] + ' <' + pattern['predicate'] + '> ' + pattern['object'] + '.'


def triple_patterns_to_query(patterns, name1, name2):

    query = 'SELECT COUNT(*) WHERE {\n'
    query += '    GRAPH <http://localhost:8890/' + name1 + '> {\n'
    for pattern in patterns:
        if pattern['source'] == "M1":
            query += '        ' + triple_pattern_to_sparql(pattern) + '\n'
    query += '    }.\n'
    query += '    GRAPH <http://localhost:8890/' + name2 + '> {\n'
    for pattern in patterns:
        if pattern['source'] == "M2":
            query += '        ' + triple_pattern_to_sparql(pattern) + '\n'
    query += '    }\n'
    query += '}'

    return query


# Return true if one and only one pattern is in common between the two queries
def one_and_only_one_common_triple_pattern(big_query, size_2_query):
    if size_2_query[0] in big_query:
        if size_2_query[1] in big_query:
            return False
        else:
            return True
    else:
        if size_2_query[1] in big_query:
            return True
        else:
            return False


# Concatenate two queries by living out one triple pattern that served as a joining point.
def merge(big_query, size_2_query):
    new_query = []

    for triple_pattern in big_query:
        new_query.append(triple_pattern)
    for triple_pattern in size_2_query:
        if triple_pattern not in new_query:
            new_query.append(triple_pattern)

    return new_query


# Create an id to index queries in order to not execute twice the same query
def make_id(list_triple_patterns):
    # We first order queries alphabetically based on the predicate
    ordered_queries = []

    for triple_pattern in list_triple_patterns:
        i = 0
        found = False
        while i < len(ordered_queries) and not found:
            if triple_pattern['predicate'] == ordered_queries[i]['predicate']:
                if triple_pattern['predicate'] == 'a':
                    if triple_pattern['object'] == ordered_queries[i]['object']:
                        found = True
                    else:
                        i += 1
                else:
                    # Same predicate but not 'a' means it's twice the same triple pattern that originate from both mappings,
                    # in this case we keep the two patterns and use the one with "M1" first for the id,
                    # followed by the other
                    if triple_pattern['source'] == 'M1':
                        found = True
                    else:
                        found = True
                        i += 1
            else:
                if triple_pattern['predicate'] < ordered_queries[i]['predicate']:
                    found = True
                else:
                    i += 1
        ordered_queries.insert(i, triple_pattern)

    # Creation of the id by concatenating the triple_patterns and changing the variable names.
    result_id = ""
    k = 0
    already_seen_variable = {}
    for triple_pattern in ordered_queries:
        if triple_pattern['subject'] not in already_seen_variable:
            already_seen_variable[triple_pattern['subject']] = "?v" + str(k)
            k += 1
        result_id += already_seen_variable[triple_pattern['subject']]

        result_id += triple_pattern['predicate']

        if triple_pattern['object'] not in already_seen_variable:
            already_seen_variable[triple_pattern['object']] = "?v" + str(k)
            k += 1
        result_id += already_seen_variable[triple_pattern['object']]
    return result_id


def create_queries(pair):

    # Store results
    list_biggest_queries = []

    # Our endpoint
    endpoint = SPARQLWrapper("http://localhost:8890/sparql")
    endpoint.setReturnFormat(JSON)

    new_bgp_list = []
    for bgp in pair['triple_patterns']:

        print()
        print()
        print("NEW BGP")
        print()
        print()

        # Will index queries (and their result) that were already asked to our endpoint, so that we don't reask them.
        indexed_queries = {"2": {}}     # "2" will store queries of size 2, other index will be created for bigger queries

        # Separate pattern with both source in two different triple pattern for each source
        bgp_m1 = []
        bgp_m2 = []

        for triple_pattern in bgp:
            if triple_pattern['source'] == 'M1':
                bgp_m1.append(
                        {'subject': triple_pattern['subject'],
                         'predicate': triple_pattern['predicate'],
                         'object': triple_pattern['object'],
                         'source': 'M1'})
            elif triple_pattern['source'] == 'M2':
                bgp_m2.append(
                        {'subject': triple_pattern['subject'],
                         'predicate': triple_pattern['predicate'],
                         'object': triple_pattern['object'],
                         'source': 'M2'})
            elif triple_pattern['source'] == 'M1 M2':
                bgp_m1.append(
                        {'subject': triple_pattern['subject'],
                         'predicate': triple_pattern['predicate'],
                         'object': triple_pattern['object'],
                         'source': 'M1'})
                bgp_m2.append(
                        {'subject': triple_pattern['subject'],
                         'predicate': triple_pattern['predicate'],
                         'object': triple_pattern['object'] + 'bis',   # add 'bis' to the object that that we wont get duplicate object variable
                         'source': 'M2'})   # the sources are now M1 for the M1 pattern and M2 for the M2 pattern in order to differentiate them4
            else:
                print("Source isn't valid. It must be 'M1', 'M2' or 'M1 M2'")
                return

        # Create queries of size 2 like so:
        # SELECT COUNT(*) WHERE {
        #     GRAPH <mapping_name1> { triple_pattern1. }.
        #     GRAPH <mapping_name2> { triple_pattern2. }
		# }
        size_2_usable_queries = []
        for tps in [[x, y] for x in bgp_m1 for y in bgp_m2]:

            # Don't do the following creation of query / testing if we already have
            key = make_id(tps)
            if key not in indexed_queries["2"]:

                # Create the sparql query out of our triple patterns
                query = triple_patterns_to_query(tps, pair['name1'], pair['name2'])

                # Test the tuple in our Virtuoso
                endpoint.setQuery(query)
                print("new query")
                print(query)
                print("size: " + str(len(tps)) + "/" + str(len(bgp)) + "   results: " + endpoint.query().convert()['results']['bindings'][0]['callret-0']['value'])
                print()

                # Keep only the tuple that return result, and memories every results
                indexed_queries["2"][key] = float(endpoint.query().convert()['results']['bindings'][0]['callret-0']['value'])
                if float(endpoint.query().convert()['results']['bindings'][0]['callret-0']['value']) > 0:  # If the query gives result
                    size_2_usable_queries.append(tps)

            else:
                if indexed_queries["2"][key] > 0:  # If the query gives result
                    print("already seen query")
                    print()
                    size_2_usable_queries.append(tps)

        # Create bigger and bigger queries as long as they return results from our endpoint
        biggest_queries = size_2_usable_queries
        usable_queries = size_2_usable_queries
        while usable_queries:
            new_usable_queries = []

            for big_query in usable_queries:
                for size_2_query in size_2_usable_queries:

                    if one_and_only_one_common_triple_pattern(big_query, size_2_query):
                        tps = merge(big_query, size_2_query)

                        if str(len(tps)) not in indexed_queries:    # create a new index for queries of new sizes
                            indexed_queries[str(len(tps))] = {}

                        if make_id(tps) not in indexed_queries[str(len(tps))]:
                            new_query = triple_patterns_to_query(tps, pair['name1'], pair['name2'])
                            endpoint.setQuery(new_query)
                            print("new query")
                            print(new_query)
                            print("size: " + str(len(tps)) + "/" + str(len(bgp)) + "   results: " + endpoint.query().convert()['results']['bindings'][0]['callret-0']['value'])
                            print()
                            indexed_queries[str(len(tps))][make_id(tps)] = float(endpoint.query().convert()['results']['bindings'][0]['callret-0']['value'])
                            if float(endpoint.query().convert()['results']['bindings'][0]['callret-0']['value']) > 0:
                                new_usable_queries.append(tps)
                        else:
                            if indexed_queries[str(len(tps))][make_id(tps)] > 0:
                                print("already seen query")
                                print()
                                new_usable_queries.append(tps)

            usable_queries = new_usable_queries
            if new_usable_queries:
                biggest_queries = new_usable_queries
        list_biggest_queries.append(biggest_queries)

    return list_biggest_queries
