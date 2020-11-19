def write_tecplot(base_name, col_names, data, station_names=None):
    for s in range(data.shape[2]):
        name = '{}_{}.dat'.format(base_name, station_names[s] if station_names else s)
        with open(name, 'w') as f:
            f.write('TITLE = "Temporal signal for station {}"\n'.format(s))
            f.write('VARIABLES = {}\n'.format(','.join(['"{}"'.format(cn) for cn in col_names])))
            for t in range(data.shape[1]):
                f.write(' '.join([str(data[q, t, s]) for q in range(data.shape[0])]))
                f.write('\n')
