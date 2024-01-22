""" Process GHSL Urban centers data of cities and population into a
shapefile."""

import geopandas as gpd


def main():
    data_path = "../data/"

    ifile_path_1 = (
        data_path + "input/GHS_STAT_UCDB2015MT_GLOBE_R2019A/"
        "GHS_STAT_UCDB2015MT_GLOBE_R2019A_V1_2.gpkg"
    )

    ifile_path_2 = (
        data_path + "input/GHS_FUA_UCDB2015_GLOBE_R2019A_54009_1K_V1_0/"
        "GHS_FUA_UCDB2015_GLOBE_R2019A_54009_1K_V1_0.gpkg"
    )

    ofile_path_1 = data_path + "output/cities/cities_uc.gpkg"
    ofile_path_2 = data_path + "output/cities/cities_fua.gpkg"

    gdf_uc = gpd.read_file(ifile_path_1)
    gdf_fua = gpd.read_file(ifile_path_2)
    gdf_fua = gdf_fua.to_crs(gdf_uc.crs)
    gdf_fua.UC_IDs = gdf_fua.UC_IDs.str.split(";").apply(
        lambda x: [int(xx) - 1 for xx in x]
    )

    uc_names = []
    uc_geos = []
    uc_regions_L1 = []
    uc_regions = []
    for i, row in gdf_fua.iterrows():
        uc_ids = row.UC_IDs
        fua_name = row.eFUA_name
        fua_ctry = row.Cntry_name
        fua_iso = row.Cntry_ISO
        ucs = gdf_uc.iloc[uc_ids]
        if fua_ctry in ucs.CTR_MN_NM.to_list():
            ucs = ucs[ucs.CTR_MN_NM == fua_ctry]
        if fua_iso in ucs.CTR_MN_ISO.to_list():
            ucs = ucs[ucs.CTR_MN_ISO == fua_iso]
        if fua_name in ucs.UC_NM_MN.to_list():
            uc = ucs[ucs.UC_NM_MN == fua_name]
            if len(uc) > 1:
                uc = ucs[ucs.P15 == ucs.P15.max()]
        else:
            uc = ucs[ucs.P15 == ucs.P15.max()]
        assert len(uc) == 1, print(gdf_uc.iloc[uc_ids])
        uc_name = uc.UC_NM_MN.item()
        uc_geo = uc.geometry.item()
        uc_region_L1 = uc.GRGN_L1.item()
        uc_region = uc.GRGN_L2.item()
        uc_names.append(uc_name)
        uc_geos.append(uc_geo)
        uc_regions_L1.append(uc_region_L1)
        uc_regions.append(uc_region)

    ghsl_fua = gdf_fua.copy()
    ghsl_fua["UC_name"] = uc_names
    ghsl_fua["UC_geo"] = uc_geos
    ghsl_fua["UC_region_L1"] = uc_regions_L1
    ghsl_fua["UC_region"] = uc_regions
    ghsl_fua = ghsl_fua[ghsl_fua.UC_p_2015 > 100000]
    region = "Latin America and the Caribbean"
    ghsl_fua = ghsl_fua[ghsl_fua.UC_region_L1 == region]
    ghsl_fua.drop(columns=["UC_region_L1"], axis=1, inplace=True)

    col_dict = {"Cntry_name": "country", "UC_region": "region", "eFUA_name": "city"}
    ghsl_fua.rename(columns=col_dict, inplace=True)

    ghsl_fua.drop(columns=["UC_geo", "UC_IDs"]).to_file(ofile_path_2)
    ghsl_fua.drop(columns=["geometry", "UC_IDs"]).rename(
        columns={"UC_geo": "geometry"}
    ).set_geometry("geometry").to_file(ofile_path_1)


if __name__ == "__main__":
    main()
