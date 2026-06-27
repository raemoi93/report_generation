def simple_avg(regular_courses):
    graded = [c['석차등급'] for c in regular_courses if c['석차등급'] is not None]
    if not graded:
        return 0.0
    return round(sum(graded) / len(graded), 2)


def weighted_avg(regular_courses):
    graded = [(c['석차등급'], c['단위수']) for c in regular_courses if c['석차등급'] is not None]
    if not graded:
        return 0.0
    total_weighted = sum(g * u for g, u in graded)
    total_units = sum(u for _, u in graded)
    return round(total_weighted / total_units, 2)


def compute_all_averages(all_semesters):
    result = {}
    for sem_key, data in all_semesters.items():
        result[sem_key] = {
            'simple': simple_avg(data['정규']),
            'weighted': weighted_avg(data['정규']),
        }
    return result


def compute_final_average(all_semesters):
    all_regular = []
    for data in all_semesters.values():
        all_regular.extend(data['정규'])
    return simple_avg(all_regular), weighted_avg(all_regular)
