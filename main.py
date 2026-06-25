import pandas as pd
from pypogo.pokemon import Pokemon

# File paths
INPUT_CSV = 'pokemon_data.csv'
OUTPUT_CSV = 'pokemon_ranks_wide.csv'

# League setup
LEAGUES = {
    'little_cup': 500,
    'great_league': 1500,
    'ultra_league': 2500,
    'master_league': 9999
}

if __name__ == "__main__":
    df = pd.read_csv(INPUT_CSV,delimiter=';')
    results = []

    for index, row in df.iterrows():
        base_name = row['pokemon_name']
        cp = row['cp']
        iv = row['iv']

        try:
            iva, ivd, ivs = map(int, iv.split('/'))
        except ValueError:
            print(f"[!] Invalid IV at row {index}: '{iv}'")
            results.append({
                'base_pokemon': base_name,
                'cp': cp,
                'iv': iv,
                'error': 'invalid_iv'
            })
            continue

        # Try to fetch family members (evolutions)
        try:
            base_pokemon = Pokemon(base_name,ivs=[iva, ivd, ivs],cp=cp)
            evolutions = list(base_pokemon.family(ancestors=False))
            family_members = [base_pokemon] + evolutions
        except Exception as e:
            print(f"[!] Error loading family for {base_name}: {e}")
            results.append({
                'base_pokemon': base_name,
                'cp': cp,
                'iv': iv,
                'error': 'family_error'
            })
            continue

        result_row = {
            'base_pokemon': base_name,
            'cp': cp,
            'iv': iv,
        }

        #print(base_pokemon.get_evolution_cps())

        for mon in family_members:
            mon_name = mon.name

            try:
                poke = Pokemon(mon_name,ivs=[iva, ivd, ivs],level=base_pokemon.level)
            except Exception as e:
                print(f"[!] Failed to load {mon_name}: {e}")
                for league in LEAGUES:
                    result_row[f"{mon_name}_{league}"] = "load_error"
                continue

            #print(f'{mon_name}cp={poke.cp}')

            for league_name, max_cp in LEAGUES.items():
                if poke.cp > max_cp:
                    rank = '-'
                else:
                    try:
                        lc_df = poke.league_ranking_table(max_cp=max_cp,max_level=50)
                        iv_row = lc_df[
                            (lc_df['iva'] == iva) &
                            (lc_df['ivd'] == ivd) &
                            (lc_df['ivs'] == ivs)
                        ]
                        if not iv_row.empty:
                            rank = int(iv_row.iloc[0]['rank'])
                        else:
                            rank = 'not_found'
                    except Exception as e:
                        print(f"[!] Error for {mon_name} in {league_name}: {e}")
                        rank = 'error'

                result_row[f"{mon_name}_{league_name}"] = rank

            

        results.append(result_row)

    # Convert and export
    output_df = pd.DataFrame(results)
    output_df.to_csv(OUTPUT_CSV, index=False,sep=';')

    print(f"\n✅ Wide-format results saved to: {OUTPUT_CSV}")
