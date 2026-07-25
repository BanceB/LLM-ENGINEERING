import anthropic
client = anthropic.Anthropic()



def seuil(MODELE, SYSTEM):

    nb = client.messages.count_tokens(
        model=MODELE, system=SYSTEM,
        messages=[{"role": "user", "content": "x"}],
    ).input_tokens
    print(f"Taille du préfixe : {nb} tokens (seuil Haiku 4.5 = 4096)")
    if nb >= 4096:
         print("→ cacheable" )
         return True
    else:
        print("→ TROP COURT, augmentez le nombre d'articles")

        return False