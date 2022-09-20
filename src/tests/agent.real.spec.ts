import { Initialize } from 'forta-agent';

const config = require('../../bot-config.json');

import { DataContainer, HandleContract } from '../types';
import { getEthersForkProvider } from '../utils';
import agent from '../agent';

const { provideInitialize, provideHandleContract } = agent;

describe('real-world tests', () => {
  jest.setTimeout(5 * 60 * 1000);

  let data: DataContainer = {} as DataContainer;
  let handleContract: HandleContract;
  let initialize: Initialize;

  beforeAll(() => {
    handleContract = provideHandleContract(data, getEthersForkProvider);
    initialize = provideInitialize(data, config, handleContract);
  });

  beforeEach(async () => {
    await initialize();
  });

  it('contract with a withdraw function #1', async () => {
    await handleContract({
      address: '0x1678454cf3d4a1a5b1064fe9307e909c9f0510d8',
      deployer: '0xe7ea0762ba7990759e75adc2ec64c70dbb1bd92e',
      blockNumber: 15570000,
    });
    expect(data.findings).toHaveLength(0);
  });

  it('contract with a withdraw function #2', async () => {
    await handleContract({
      address: '0x5c111745e05bc630ced89a63aa74254c3dcde12a',
      deployer: '0xc69b9b52e1e4cf384894199290cda5f9e94ae1b6',
      blockNumber: 15569936,
    });
    expect(data.findings).toHaveLength(0);
  });

  it('contract with a withdraw function #3', async () => {
    await handleContract({
      address: '0x8592cae3420d89765dcd77152a2077909e029267',
      deployer: '0x4ecbac578acd7f9928a3d0f7e0b7ec0d54a7e3b5',
      blockNumber: 15570386,
    });
    expect(data.findings).toHaveLength(0);
  });

  it('Saddle Finance attack', async () => {
    await handleContract({
      address: '0x7336f819775b1d31ea472681d70ce7a903482191',
      deployer: '0x63341ba917de90498f3903b199df5699b4a55ac0',
      blockNumber: 14684300,
    });
    expect(data.findings).toHaveLength(1);
  });

  it('FEGToken attack', async () => {
    await handleContract({
      address: '0xf02b075f514c34df0c3d5cb7ebadf50d74a6fb17',
      deployer: '0xf99e5f80486426e7d3e3921269ffee9c2da258e2',
      blockNumber: 14789154,
    });
    expect(data.findings).toHaveLength(1);
  });

  it('Devour attack (payable function)', async () => {
    await handleContract({
      address: '0x9e7f9123ce12060ec844ac56de047cc50a827201',
      deployer: '0x9448368ff76b6698c59ca940b1ee2bf7fba0bc21',
      blockNumber: 15503993,
    });
    expect(data.findings).toHaveLength(1);
  });
});
