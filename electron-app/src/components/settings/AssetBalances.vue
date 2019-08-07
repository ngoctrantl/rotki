<template>
  <div class="asset-balances">
    <v-layout>
      <v-flex>
        <h3 class="text-center">{{ title }}</h3>
      </v-flex>
    </v-layout>
    <v-data-table :headers="headers" :items="balances">
      <template #header.usdValue>
        {{ currency.ticker_symbol }} value
      </template>
      <template #item.asset="{ item }">
        <span class="asset-balances__balance__asset">
          <crypto-icon
            width="26px"
            class="asset-balances__balance__asset__icon"
            :symbol="item.asset"
          ></crypto-icon>
          {{ item.asset }}
        </span>
      </template>
      <template #item.amount="{ item }">
        {{ item.amount | formatPrice(floatingPrecision) }}
      </template>
      <template #item.usdValue="{ item }">
        {{
          item.usdValue
            | calculatePrice(exchangeRate(currency.ticker_symbol))
            | formatPrice(floatingPrecision)
        }}
      </template>
      <template v-if="items && items.length > 0" #body.append="{ items }">
        <tr class="asset-balances__totals">
          <td>Totals</td>
          <td></td>
          <td>
            {{
              items.map(val => val.usdValue)
                | balanceSum
                | calculatePrice(exchangeRate(currency.ticker_symbol))
                | formatPrice(floatingPrecision)
            }}
          </td>
        </tr>
      </template>
    </v-data-table>
  </div>
</template>

<script lang="ts">
import { Component, Prop, Vue } from 'vue-property-decorator';
import { AssetBalance } from '@/model/blockchain-balances';
import { mapGetters, mapState } from 'vuex';
import CryptoIcon from '@/components/CryptoIcon.vue';
import { Currency } from '@/model/currency';

@Component({
  components: { CryptoIcon },
  computed: {
    ...mapState(['currency']),
    ...mapGetters(['exchangeRate', 'floatingPrecision'])
  }
})
export default class AssetBalances extends Vue {
  @Prop({ required: true })
  balances!: AssetBalance[];
  @Prop({ required: true })
  title!: string;

  currency!: Currency;
  floatingPrecision!: number;
  exchangeRate!: (currency: string) => number;

  headers = [
    { text: 'Asset', value: 'asset' },
    { text: 'Amount', value: 'amount' },
    { text: 'USD Value', value: 'usdValue' }
  ];
}
</script>

<style scoped lang="scss">
.asset-balances {
  margin-top: 16px;
  margin-bottom: 16px;
}

.asset-balances__balance__asset {
  display: flex;
  flex-direction: row;
  align-items: center;
}

.asset-balances__balance__asset__icon {
  margin-right: 8px;
}

.asset-balances__totals {
  font-weight: 500;
}
</style>