#ifndef VXL_C_H
#define VXL_C_H

#include <bitset>

#ifdef _MSC_VER
#include <hash_map>
#define map_type stdext::hash_map
#else
#include <tr1/unordered_map>
#define map_type std::tr1::unordered_map
#endif

#define MAP_X 512
#define MAP_Y 512
#define MAP_Z 64
#define get_pos(x, y, z) (x + (y) * MAP_Y + (z) * MAP_X * MAP_Y)
#define DEFAULT_COLOR 0xFF674028

struct MapData
{
    std::bitset<MAP_X * MAP_Y * MAP_Z> geometry;
    map_type<int, int> colors;
};

int inline get_solid(int x, int y, int z, MapData * map)
{
    return map->geometry[get_pos(x, y, z)];
}

int inline get_color(int x, int y, int z, MapData * map)
{
    map_type<int, int>::const_iterator iter = map->colors.find(
        get_pos(x, y, z));
    if (iter == map->colors.end())
        return 0;
    return iter->second;
}

void inline set_point(int x, int y, int z, MapData * map, bool solid, int color)
{
    int i = get_pos(x, y, z);
    map->geometry[i] = solid;
    if (!solid)
        map->colors.erase(i);
    else
        map->colors[i] = color;
}

void inline set_column_solid(int x, int y, int z_start, int z_end,
    MapData * map, bool solid)
{
    int i = get_pos(x, y, z_start);
    int i_end = get_pos(x, y, z_end);
    if (!solid)
    {
        while (i <= i_end)
        {
            map->geometry[i] = solid;
            i += MAP_X * MAP_Y;
        }
    }
    else
    {
        while (i <= i_end)
        {
            map->geometry[i] = solid;
            i += MAP_X * MAP_Y;
        }
    }
}

void inline set_column_color(int x, int y, int z_start, int z_end,
    MapData * map, int color)
{
    int i = get_pos(x, y, z_start);
    int i_end = get_pos(x, y, z_end);
    while (i <= i_end)
    {
        map->colors[i] = color;
        i += MAP_X * MAP_Y;
    }
}

#endif /* VXL_C_H */