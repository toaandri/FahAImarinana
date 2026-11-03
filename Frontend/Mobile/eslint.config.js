// https://docs.expo.dev/guides/using-eslint/
const { defineConfig } = require('eslint/config');
const expoConfig = require('eslint-config-expo/flat');

module.exports = defineConfig([
  expoConfig,
  {
    ignores: ['dist/*'],
    languageOptions: {
      globals: {
        __dirname: 'readonly',
      },
    },
    rules: {
      'no-restricted-syntax': [
        'error',
        {
          selector:
            'JSXElement[openingElement.name.name=/^(View|Pressable|ScrollView|SafeAreaView|TouchableOpacity|TouchableHighlight)$/] > JSXText[value=/\\S/]',
          message: 'Le texte doit être placé dans un composant <Text>.',
        },
      ],
    },
  },
]);
