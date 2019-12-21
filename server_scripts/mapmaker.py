from geojson import Feature, Point, LineString

def createPopulationsGeoJson(populations):
    """ populations is the populations table read from db.getPopulations()
        output: a GeoJSON object with a marker for each population location
    """
    population_markers = []
    for p in populations:
        point = Point([p['lon'], p['lat']])
        properties = {
            'title': p['name'] + ': ' + str(p['pr']),
            'marker-symbol': 'city',
            'marker-color': '#ff2200',
            'marker-size': 'large'
        }
        population_markers.append(Feature(geometry = point, properties = properties))

    return(population_markers)


def createLocationsGeoJson(plants):
    """ plants is the plants table read from db.getPlants()
        output: a GeoJSON object with a marker for each plant location
    """
    plant_markers = []
    for p in plants:
        point = Point([p['lon'], p['lat']])
        if p['existing_location']:
            marker_title = p['locationname'] + ': ' + 'existing location'
        else:
            marker_title = p['locationname'] + ': ' + 'new location'
        properties = {
            'title': marker_title,
            'marker-symbol': 'water',
            'marker-color': '#3bb2d0',
            'marker-size': 'large'
        }
        plant_markers.append(Feature(geometry = point, properties = properties))

    return(plant_markers)

def createLocationsSolutionsGeoJson(plants, solution_details):
    """ create an array of GeoJson objects, each object for a solution
        plants: plants table read from db.getPlants()
        solution_details: transformed table of binary data (currently reading from output/transformed output.csv)
    """
    solution_locations = []
    current_solution = []
    for i in range(len(solution_details)):
        row = solution_details[i]
        solutionID = int(row[0])
        # -- get this location information and add to current_solution -- 
        if row[5] not in (None, ""):    # only add if this location is being utilized in the current solution
            locationID = int(row[1]) # locationID of the row we're looking at
            # find info of this locationID
            plant_info = [(p['lon'], p['lat'], p['locationname'], p['existing_location']) for p in plants if p['index']==locationID][0]
            point = Point([plant_info[0], plant_info[1]])
            if plant_info[3]: # if existing location
                marker_title = plant_info[2] + ': ' + 'existing location'
            else:
                marker_title = plant_info[2]+ ': ' + 'new location'
            properties = {
                'title': marker_title,
                'marker-symbol': 'water',
                'marker-color': '#3bb2d0',
                'marker-size': 'large'
            }
            current_solution.append(Feature(geometry = point, properties = properties))
        # -- done adding this location to current_solution

        # check if we found the last line of the current solutionID
        if i==len(solution_details)-1 or solutionID!=int(solution_details[i+1][0]):
            # If so, append the finished solution to solution_locations and reset current_solution
            solution_locations.append(current_solution)
            current_solution = []
            # (only safety check) check if locationID is the same as its index on solutions_locations
            if solutionID != (len(solution_locations)):
                raise Exception('solutionID found in transformed output data does not align with its index')

    return(solution_locations)

def createLocationClusterLinestringGeoJson(plants, populations, solution_details):
    """ create an array of GeoJson objects, each object for a solution and is a set of LineString connecting plants and population clusters
        plants: plants table read from db.getPlants()
        populations: populations table read from db.getPopulation()
        solution_details: transformed table of binary data (currently reading from output/transformed output.csv)
    """
    solution_locations = [] # output array
    current_solution = []   # array of LineString for current solution
    for i in range(len(solution_details)):
        row = solution_details[i]
        solutionID = int(row[0])
        # check if this location is being utilized in the current location
        if row[5] not in (None, ""):
            # find lonlat of location
            locationID = int(row[1]) # locationID of the row we're looking at
            plant_lonlat = [(p['lon'], p['lat']) for p in plants if p['index']==locationID][0]
            # find population clusters connected to this location
            connected_clusters = [int(popID) for popID in row[5].split(',')] # this return an array of int populationID
            # find lonlat of connected clusters and form LineString with plant's lonlat
            for popID in connected_clusters:
                pop_lonlat = [(p['lon'], p['lat']) for p in populations if p['index']==popID][0]
                current_solution.append(
                    Feature(geometry = LineString([plant_lonlat, pop_lonlat]))
                )
        # -- done adding this location to current_solution
        # check if we found the last line of the current solutionID
        if i==len(solution_details)-1 or solutionID!=int(solution_details[i+1][0]):
            # If so, append the finished solution to solution_locations and reset current_solution
            solution_locations.append(current_solution)
            current_solution = []
            # (only safety check) check if locationID is the same as its index on solutions_locations
            if solutionID != (len(solution_locations)):
                raise Exception('solutionID found in transformed output data does not align with its index')
    return(solution_locations)