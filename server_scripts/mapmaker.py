from geojson import Feature, Point

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