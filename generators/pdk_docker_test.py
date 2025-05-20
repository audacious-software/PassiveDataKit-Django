# pylint: disable=line-too-long

def generator_name(identifier): # pylint: disable=unused-argument
    return 'Docker Setup Test Point'

def update_data_type_definition(definition):
    if 'message' in definition:
        definition['message']['pdk_variable_name'] = 'Message'
        definition['message']['pdk_variable_description'] = 'Should always read "If you see this data point in the data points table, your Docker setup was a success."'
        definition['level']['pdk_codebook_group'] = 'Passive Data Kit: Docker Setup'
        definition['level']['pdk_codebook_order'] = 0

    del definition['observed']

    definition['pdk_description'] = 'Generated to validate that a Docker container setup was successful.'
